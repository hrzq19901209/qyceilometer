import six
import inspect 

class NotImplemetedError(Exception):
	pass

class Model(object):
	def __init__(self, **kwds):
		self.fields = list(kwds)
		for k, v in six.iteritems(kwds):
			setattr(self,k ,v)

	def as_dict(self):
		d = {}
		for f in self.fields:
			v = getattr(self, f)
			if isinstance(v, Model):
				v = v.as_dict()
			elif isinstance(v, list) and v and isinstance(v[0], Model):
				v = [sub.as_dict for sub in v]
			d[f] = v
		return d 

	def __eq__(self, other):
		if isinstance(other, Model):
			return self.as_dict() == other.as_dict()
		else:
			return False

	@classmethod
	def get_field_names(cls):
		fields = inspect.getargspec(cls.__init__)[0]
		return set(fields) - set("self")


