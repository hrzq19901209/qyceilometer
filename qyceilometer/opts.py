import qyceilometer.service as service
import qyceilometer.storage.mongo.utils as utils

def list_opts():
	return [
	    ('logging', service.OPTS),
	    ('database', utils.OPTS),
	]