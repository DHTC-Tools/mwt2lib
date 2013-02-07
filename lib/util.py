

def uniq(items):
	return list(set(items))


def units(n, precision=2):
	suffices = [''] + list('KMGTPEZY')
	while n >= 1000 and suffices:
		n /= 1000.0
		suffices = suffices[1:]
	fmt = '%%.%dg%%sB' % precision
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


