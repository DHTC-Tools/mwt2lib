#
# We might conceivably allow any of several key/value interfaces -- memcache,
# redis, ....  The goal of this module is to provide an abstraction layer to
# support any that we need.
#
# We're not there yet though.  For this first pass we're only
# supporting memcache.

# standard
import time

# local
import util

# optional/recommended
memcache = util.importer('memcache')


class KVStoreError(Exception): pass
class UnsupportedDriverError(KVStoreError): pass


class kvstore(object):
	def __init__(self, connect, log=None, prefix=''):
		if connect.startswith('memcache://'):
			if memcache is None:
				raise UnsupportedDriverError, 'memcache support is not available'

			self.type = 'memcache'
			self.module = memcache
			self.prefix = prefix
			addr = connect[11:].strip('/')
			self.db = memcache.Client([addr])

			if log:
				self.log = self._deferredlog
				self._deferredlogfile = log
			else:
				self.log = self._nolog

			self.log('connect to %s' % connect)


	def _key(self, key):
		# prefix key with the prefix associated at init, unless it begins
		# with '.'.  In that case, take it literally except for the '.'.
		if key[0] == '.':
			return key[1:]
		else:
			return self.prefix + key


	def __setitem__(self, key, value):
		key = self._key(key)
		if self.module == memcache:
			self.db.set(key, value)
			self.log('%s = %s' % (key, value))
			return

		raise UnsupportedDriverError, 'instance uses unknown driver'


	def __getitem__(self, key):
		key = self._key(key)
		if self.module == memcache:
			return self.db.get(key)
		raise UnsupportedDriverError, 'instance uses unknown driver'


	def close(self):
		self.log('close')


	def _nolog(self, *msgs):
		return

	def _deferredlog(self, *msgs):
		self.logfp = open(self._deferredlogfile, 'a')
		self.log = self._log
		self.log(*msgs)

	def _log(self, *msgs):
		if not self.logfp:
			return
		t = time.ctime()
		for msg in msgs:
			self.logfp.write('%s <%x>: %s\n' % (t, id(self.db), msg))


	def __call__(self, method, *args):
		return getitem(self.db, method)(*args)
