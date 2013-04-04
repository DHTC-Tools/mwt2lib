import re


def uniq(items):
	return list(set(items))


def units(n, precision=2):
	suffices = [''] + list('KMGTPEZY')
	while n >= 1000 and suffices:
		n /= 1000.0
		suffices = suffices[1:]
	fmt = '%%.%df%%sB' % precision
	return fmt % (n, suffices[0])


def importer(*args):
	module = None
	if args and ' ' in args[0]:
		args = args[0].split()
	for arg in args:
		try:
			module = __import__(arg)
			break
		except ImportError:
			pass

	return module


class jsdict(dict):
	'''Dict that works like a javascript dict.	In python lingo, attrs and
	items function the same.'''

	def __setitem__(self, key, value):
		key = key.lower()
		dict.__setitem__(self, key, value)

	def __getitem__(self, key):
		key = key.lower()
		return dict.__getitem__(self, key)

	def __setattr__(self, key, value):
		key = key.lower()
		dict.__setitem__(self, key, value)

	def __getattr__(self, key):
		key = key.lower()
		return dict.__getitem__(self, key)


class cache(dict):
	'''A dictionary that acts as a cache to a lookup function.'''
	def __init__(self, lookup):
		self._lookup = lookup
		dict.__init__(self)

	def __getitem__(self, key):
		if key not in self:
			self[key] = self._lookup(key)
		return dict.__getitem__(self, key)


class formatter(object):
	'''formatter is a generalized string-templating class.

	A template contains variables expressed within {curly braces}.  When
	a formatter is instantiated, the instance is a callable which accepts
	a template as an argument and returns the formatted result.

	At initialization, a formatter takes an arbitrary list of arguments,
	which we term 'resolvers'.  Each resolver is used in turn to attempt
	to resolve a template variable.  A resolver may be:
	  * a callable, which takes the template variable as argument and
	    returns the expansion of that variable;
	  * a dictionary, which returns the result of 'resolver[variable]';
	  * an object, which returns the result of 'resolver.variable';
	  * a string or unicode string, which returns itself

	Examples:
	fmtr = formatter(lambda x: rot13(x))
	fmtr('abc.{abc}') -> 'abc.nop'

	x = { 'abc': 'alphabet' }
	fmtr = formatter(x)
	fmtr('{abc}') -> 'abc'
	fmtr('{abc}.{xyz}') -> 'abc.'

	x = { 'abc': 'alphabet' }
	fmtr = formatter(x, 'nevermind')
	fmtr('{abc}.{xyz}') -> 'abc.nevermind'

	class X(object): pass
	x = X()
	x.foo = 'bar'
	fmtr = formatter(x, rot13)
	fmtr('{foo}.{xyz}') -> 'bar.klm'
	'''

	rx = re.compile('{([^}]+)}')

	def __init__(self, *args):
		self.resolvers = args

	def __call__(self, s):
		def resolver(match):
			key = match.group(1)
			for res in self.resolvers:
				if callable(res):
					return str(res(key))
				if hasattr(res, '__contains__') and key in res:
					return str(res[key])
				if hasattr(res, key):
					return str(getattr(res, key))
				if type(res) in (type(''), type(u'')):
					return res
			return ''
		return self.rx.sub(resolver, s)
