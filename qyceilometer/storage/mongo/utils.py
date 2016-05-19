import pymongo
import weakref
import logging
import time
from oslo_config import cfg
from oslo_utils import netutils

LOG = logging.getLogger(__name__)

ERROR_INDEX_WITH_DIFFERENT_SPEC_ALREADY_EXISTS = 86
MONGO_METHODS = set([typ for typ in dir(pymongo.collection.Collection)
                     if not typ.startswith('_')])

OPTS = [
    cfg.IntOpt('max_retries',default=3,
            help=('(required) the max times try to connect the db')),
    cfg.IntOpt('retry_interval',default=3,
            help=('(required) the interval between retry to connect the db')),
    cfg.StrOpt('connection',default='',
            help=('(required) where is the mongodb?')),
]

cfg.CONF.register_opts(OPTS, group='database')

class ConnectionPool(object):

	def __init__(self):
		self._pool = {}

	def connect(self):
		url = cfg.CONF.database.connection
		if not url:
			LOG.error('Can not get the address of the sourcedatabase, please set up in the qyceilometer.conf')
			raise
		connection_options = pymongo.uri_parser.parse_uri(url)
		del connection_options['database']
		del connection_options['username']
		del connection_options['password']
		del connection_options['collection']
		pool_key = tuple(connection_options)
		
		if pool_key in self._pool:
			client = self._pool.get(pool_key)()
			if client:
				return client

		splitted_url = netutils.urlsplit(url)
		log_data = {'db': splitted_url.scheme,
					'nodelist': connection_options['nodelist']}
		LOG.info(('Connecting to %(db)s on %(nodelist)s') % log_data)
		client = self._mongo_connect(url)
		LOG.info(('Connectted to %(db)s on %(nodelist)s') % log_data)
		self._pool[pool_key] = weakref.ref(client)
		connection_options = pymongo.uri_parser.parse_uri(url)
		db = getattr(client, connection_options['database'])
		return db

	@staticmethod
	def _mongo_connect(url):
		try:
			client = MongoProxy(pymongo.MongoClient(url))
			return client
		except pymongo.errors.ConnectionFailure as e:
			LOG.warn(('Unable to connect to the database servers:'
				'%(errmsg)s.') % {'errmsg': e})
		raise

def safe_mongo_call(call):
	def closure(*args, **kwargs):
		max_retries = cfg.CONF.database.max_retries
		retry_interval = cfg.CONF.database.retry_interval
		attempts = 0
		while True:
			try:
				return call(*args, **kwargs)
			except pymongo.errors.AutoReconnect as err:
				if 0 <= max_retries <= attempts:
					LOG.error('Unable to reconnect to the primary mongodb' 
						'after %(retries)d retries. Giving up.' % 
						{'retries': max_retries})
					raise
				LOG.warn(('Unable to reconnect to primary mongodb:'
					'%(errmsg)s. Trying again in %(retry_interval)d '
					'seconds.') %
					{'errmsg': err, 'retry_interval': retry_interval})
				attempts += 1
				time.sleep(retry_interval)
	return closure

class MongoProxy(object):
	def __init__(self, conn):
		self.conn = conn

	def __getitem__(self, item):
		return MongoProxy(self.conn[item])

	def find(self, *args, **kwargs):
		return CursorProxy(self.conn.find(*args, **kwargs))

	def create_index(self, keys, name=None, *args, **kwargs):
		try:
			self.conn.create_index(keys, name=name, *args, **kwargs)
		except pymongo.errors.OperationFailure as e:
			if e.code is ERROR_INDEX_WITH_DIFFERENT_SPEC_ALREADY_EXISTS:
				LOG.info(('index %s will be recreated.') % name)
				self._recreate_index(keys, name, *args, **kwargs)

	@safe_mongo_call
	def _recreate_index(self, keys, name, *args, **kwargs):
		self.conn.drop_index(name)
		self.conn.create_index(keys, name=name, *args, **kwargs)

	def __getattr__(self, item):
		if item in ('item', 'database'):
			return getattr(self.conn, item)
		if item in MONGO_METHODS:
			return MongoConn(getattr(self.conn, item))
		return MongoProxy(getattr(self.conn, item))

	def __call__(self, *args, **kwargs):
		return self.conn(*args, **kwargs)



class MongoConn(object):
    def __init__(self, method):
        self.method = method

    @safe_mongo_call
    def __call__(self, *args, **kwargs):
        return self.method(*args, **kwargs)


class CursorProxy(pymongo.cursor.Cursor):
	def __init__(self, cursor):
		self.cursor = cursor

	def __getitem__(self, item):
		return self.cursor[item]

	@safe_mongo_call
	def next(self):
		try:
			save_cursor = self.cursor.clone()
			return self.cursor.next()
		except pymongo.errors.AutoReconnect:
			self.cursor = save_cursor
			raise

	def __getattr__(self, item):
		return getattr(self.cursor, item)