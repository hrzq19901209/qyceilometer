from qyceilometer.storage.mongo import utils
from qyceilometer.storage import model
from oslo_config import cfg 
import logging

import pymongo
import datetime

default_opts = [
        cfg.StrOpt('connection',default='',
            help=('')),
]

cfg.CONF.register_opts(default_opts,group='database')

LOG = logging.getLogger(__name__)

def hour_collection():
    LOG.info('hour hour_collection started!')
    url = getattr(getattr(cfg.CONF,"database"), "connection")
    if not url:
        LOG.error('Can not get the address of the sourcedatabase, please set up in the qyceilometer.conf')
        raise

    c = utils.ConnectionPool().connect(url)
    connection_options = pymongo.uri_parser.parse_uri(url)
    db = getattr(c, connection_options['database'])
    resources = db.resource.find(sort=[('timestamp',pymongo.DESCENDING)])
    meters = []
    for resource in resources:
        for meter in resource['meter']:
            m = model.Meter(meter['counter_name'],meter['counter_type'],meter['counter_unit'],resource['_id'],resource['project_id'],resource['user_id'])
            meters.append(m)

    today = datetime.date.today()-datetime.timedelta(hours=8)
    now = datetime.datetime.utcnow()
    start_time_stamp = datetime.datetime.combine(today, datetime.time(now.hour-1))
    end_time_stamp = datetime.datetime.combine(today, datetime.time(now.hour))

    for meter in meters:
        d = {}
        d['counter_name'] = meter.name
        d['resource_id'] = meter.resource_id
        d['recorded_at'] = {'$lt': end_time_stamp,'$gte': start_time_stamp}
        sample_list = db.meter.find(d)
        if getattr(meter, 'type') == 'cumulative' or getattr(meter, 'type') == 'delta':
            volume = 0
            count = 0
            for sample in sample_list:
                volume =  sample['counter_volume']
                count = count + 1
            if count != 0:
                m = model.Sample(start_time_stamp, meter.name, meter.type, meter.unit, volume, meter.user_id, meter.project_id, meter.resource_id)
                db.hour.insert(m.as_dict())

        if getattr(meter, 'type') == 'gauge':
            volume = 0
            count = 0
            for sample in sample_list:
                volume =  volume+ sample['counter_volume']
                count = count + 1
            if count != 0:
                volume = volume/count
                m = model.Sample(start_time_stamp, meter.name, meter.type, meter.unit, volume, meter.user_id, meter.project_id, meter.resource_id)
                db.hour.insert(m.as_dict())
    LOG.info('hour hour_collection completed')