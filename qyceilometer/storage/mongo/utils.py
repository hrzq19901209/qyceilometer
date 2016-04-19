import pymongo
import weakref
import logging
import time

LOG = logging.getLogger(__name__)

ERROR_INDEX_WITH_DIFFERENT_SPEC_ALREADY_EXISTS = 86
MONGO_METHODS = set([typ for typ in dir(pymongo.collection.Collection)
                     if not typ.startswith('_')])

def quote_key(key, reverse=False):
    """Prepare key for storage data in MongoDB.

    :param key: key that should be quoted
    :param reverse: boolean, True --- if we need a reverse order of the keys
                    parts
    :return: iter of quoted part of the key
    """
    r = -1 if reverse else 1

    for k in key.split('.')[::r]:
        if k.startswith('$'):
            k = parse.quote(k)
        yield k


def improve_keys(data, metaquery=False):
    """Improves keys in dict if they contained '.' or started with '$'.

    :param data: is a dictionary where keys need to be checked and improved
    :param metaquery: boolean, if True dots are not escaped from the keys
    :return: improved dictionary if keys contained dots or started with '$':
            {'a.b': 'v'} -> {'a': {'b': 'v'}}
            {'$ab': 'v'} -> {'%24ab': 'v'}
    """
    if not isinstance(data, dict):
        return data

    if metaquery:
        for key in six.iterkeys(data):
            if '.$' in key:
                key_list = []
                for k in quote_key(key):
                    key_list.append(k)
                new_key = '.'.join(key_list)
                data[new_key] = data.pop(key)
    else:
        for key, value in data.items():
            if isinstance(value, dict):
                improve_keys(value)
            if '.' in key:
                new_dict = {}
                for k in quote_key(key, reverse=True):
                    new = {}
                    new[k] = new_dict if new_dict else data.pop(key)
                    new_dict = new
                data.update(new_dict)
            else:
                if key.startswith('$'):
                    new_key = parse.quote(key)
                    data[new_key] = data.pop(key)
    return data

def unquote_keys(data):
    """Restores initial view of 'quoted' keys in dictionary data

    :param data: is a dictionary
    :return: data with restored keys if they were 'quoted'.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                unquote_keys(value)
            if key.startswith('%24'):
                k = parse.unquote(key)
                data[k] = data.pop(key)
    return data

class ConnectionPool(object):

	def __init__(self):
		self._pool = {}

	def connect(self, url):
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

		client = self._mongo_connect(url)
		self._pool[pool_key] = weakref.ref(client)
		return client

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
		max_retries = 3#cfg.CONF.database.max_retries
		retry_interval = 3#cfg.CONF.database.retry_interval
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
	def __init__(self,conn):
		self.conn = conn

	def __getitem__(self,item):
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