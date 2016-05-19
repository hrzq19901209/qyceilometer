import qyceilometer.collection.hour as hour
import qyceilometer.collection.day as day
import qyceilometer.collection.week as week
import qyceilometer.service as service
import qyceilometer.storage.mongo.utils as utils

def list_opts():
	return [
	    ('logging', hour.OPTS),
	    ('logging', day.OPTS),
	    ('logging', week.OPTS),
	    ('logging', service.OPTS),
	    ('database', utils.OPTS),
	]