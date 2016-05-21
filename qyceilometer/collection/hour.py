from qyceilometer.storage.mongo import utils
from qyceilometer.storage import model
import logging

import pymongo
import datetime
import time

LOG = logging.getLogger(__name__)

def hour_collection():
    LOG.info('hour collection started!')

    db = utils.ConnectionPool().connect()
    resources = db.resource.find()
    meters = []
    for resource in resources:
        for meter in resource['meter']:
            m = model.Meter(meter['counter_name'],meter['counter_type'],meter['counter_unit'],resource['_id'],resource['project_id'],resource['user_id'])
            meters.append(m)

    now = datetime.datetime.utcnow()
    end_time_stamp = datetime.datetime(now.year,now.month,now.day,now.hour)
    start_time_stamp = end_time_stamp - datetime.timedelta(hours=1)
    insert_time = start_time_stamp - datetime.timedelta(hours=time.timezone/3600)

    for meter in meters:
        d = {}
        d['counter_name'] = meter.name
        d['resource_id'] = meter.resource_id
        d['timestamp'] = {'$lt': end_time_stamp,'$gte': start_time_stamp}
        sample_list = db.meter.find(d)
        if getattr(meter, 'type') == 'cumulative' or getattr(meter, 'type') == 'delta':
            volume = 0
            count = 0
            for sample in sample_list:
                volume =  sample['counter_volume']
                count = count + 1
            if count != 0:
                m = model.Sample(insert_time, meter.name, meter.type, meter.unit, volume, meter.user_id, meter.project_id, meter.resource_id)
                db.hour.insert(m.as_dict())

        if getattr(meter, 'type') == 'gauge':
            volume = 0
            count = 0
            for sample in sample_list:
                volume =  volume + sample['counter_volume']
                count = count + 1
            if count != 0:
                volume = volume/count
                m = model.Sample(insert_time, meter.name, meter.type, meter.unit, volume, meter.user_id, meter.project_id, meter.resource_id)
                db.hour.insert(m.as_dict())
    LOG.info('hour collection completed')