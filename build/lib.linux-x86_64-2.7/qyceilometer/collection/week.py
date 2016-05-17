from qyceilometer.storage.mongo import utils
from qyceilometer.storage import model
from oslo_config import cfg
import logging

import pymongo
import datetime

OPTS = [
    cfg.StrOpt('log_file_week',default='/var/log/ceilometer/qyceilometer-week.log',
            help=('the log for week collection')),
]

cfg.CONF.register_opts(OPTS, group='logging')
handler = logging.FileHandler(cfg.CONF.logging.log_file_hour)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
handler.setFormatter(formatter)
LOG = logging.getLogger(__name__)
LOG.addHandler(handler)

def week_collection():
    LOG.info('week collection started!')

    db = utils.ConnectionPool().connect()
    resources = db.resource.find()
    meters = []
    for resource in resources:
        for meter in resource['meter']:
            m = model.Meter(meter['counter_name'],meter['counter_type'],meter['counter_unit'],resource['_id'],resource['project_id'],resource['user_id'])
            meters.append(m)

    now = datetime.datetime.utcnow()
    now = now - datetime.timedelta(now.weekday())
    end_time_stamp = datetime.datetime(now.year,now.month,now.day,0,0,0)
    start_time_stamp = end_time_stamp - datetime.timedelta(days=7)

    for meter in meters:
        d = {}
        d['counter_name'] = meter.name
        d['resource_id'] = meter.resource_id
        d['timestamp'] = {'$lt': end_time_stamp,'$gte': start_time_stamp}
        sample_list = db.day.find(d)
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
                volume =  volume + sample['counter_volume']
                count = count + 1
            if count != 0:
                volume = volume/count
                m = model.Sample(start_time_stamp, meter.name, meter.type, meter.unit, volume, meter.user_id, meter.project_id, meter.resource_id)
                db.day.insert(m.as_dict())
    LOG.info('week collection completed')