# standard
import os
import urllib
import re

# local
import util

class urls(object):
	dCacheUsageInfo = 'http://dcache-admin.mwt2.org:2288/usageInfo'


class DCacheException(Exception): pass
class InvalidSrmNotationError(DCacheException): pass

class dcacheusage(list):
	def __init__(self):
		fp = urllib.urlopen(urls.dCacheUsageInfo)
		self._parse(fp)
		fp.close()

	@staticmethod
	def datum(line):
		return line.replace('>', '<').split('<')[2]

	def _parse(self, fp):
		item = util.jsdict()
		for line in fp:
			if item and item.cell and '</tr>' in line:
				self.append(item)
				item = util.jsdict()

			elif line.startswith('<td class="cell">'):
				item.cell = self.datum(line)
				item.host = item.cell.split('_')[0]
			elif line.startswith('<td class="domain">'):
				item.domain = self.datum(line)
			elif line.startswith('<td class="total">'):
				item.total = int(self.datum(line))
			elif line.startswith('<td class="free">'):
				item.free = int(self.datum(line))
			elif line.startswith('<td class="precious">'):
				item.precious = int(self.datum(line))

	def pools(self):
		return sorted(util.uniq([row.cell for row in self]))

	def hosts(self):
		return sorted(util.uniq([row.host for row in self]))


class syscmd(object):
	'''A syscmd object is initialized with an arbitrary set of commands
	to be run under some shell (/bin/sh by default).  The object provides
	the usual file-like methods for reading output from the output stream,
	and is iterable.

	syscmd can be subclassed to use different shells, with optional prologue
	and epilogue commands.
	'''

	shell = '/bin/sh'
	prologue = []
	epilogue = []
	appendargs = False

	def __init__(self, *args, **kwargs):
		if 'shell' in kwargs:
			self.shell = kwargs['shell']

		if self.appendargs:
			self.shell += ' ' + ' '.join(["'%s'" % arg for arg in args])

		stdin, self.stdout = os.popen2(self.shell)

		if not self.appendargs:
			for arg in self.prologue:
				stdin.write(arg + '\n')
			for arg in args:
				stdin.write(arg + '\n')
			for arg in self.epilogue:
				stdin.write(arg + '\n')
			stdin.flush()

	def read(self, *args):
		return self.stdout.read(*args)

	def readline(self, *args):
		return self.stdout.readline(*args)

	def readlines(self, *args):
		return self.stdout.readline(*args)

	def close(self):
		return self.stdout.close()

	def __iter__(self):
		for line in self.stdout:
			yield line


class dcachecmd(syscmd):
	'''syscmd subclass for running commands under dcache-admin.'''

	shell = '/usr/local/bin/dcache-admin 2>/dev/null'
	epilogue = ['..'] * 5 + ['logoff']


class dcmd(syscmd):
	'''syscmd subclass for running commands under dcmd.

	XXX TODO: consider re-implementing dcmd, without using the dcmd.sh
	script.  There are multiple well-maintained alternatives in
	opensourcelandia (this is a common need among admins of many systems),
	or we could implement internally in python using e.g. paramiko (<3).
	Paramiko is quite nice because it implements the ssh command protocol
	internally, avoiding all the cruft associated with host key matching,
	etc.
	'''

	shell = '/usr/local/bin/dcmd.sh --timeout=120 --no-color 2>&1'
	appendargs = True


class SrmParser(object):
	_rx_res = re.compile(r'\s*([a-zA-Z]+):')

	def parse(self, line):
		o = util.jsdict()
		off = line.find(' ')
		try:
			o.id = int(line[:off])
		except ValueError:
			raise InvalidSrmNotationError

		# the srm output line is loosely structured: a sequence of key/value
		# pairs coupled with colons.  Keys are alphabetical and contain no
		# whitespace, but values may contain colons or whitespace, and are
		# unbounded.  This makes machine parsing tricky.

		line = line[off:]
		prevkey = None
		while True:
			m = self._rx_res.search(line)
			if m is None:
				break
			key = m.group(1)
			line = line[m.end(1)+1:]
			o[key] = line
			if prevkey:
				# if we had a key from a previous iteration, we truncate its
				# value at the start of our match
				o[prevkey] = o[prevkey][:m.start(1)].strip()
			prevkey = key

		return o


class SrmManager(object):
	'''Just a container for some SRM functions, really.  There's no
	shared or reused state here.
	'''

	def reservations(self):
		res = self._parsesrm_startingwith('Reservations:')
		for r in res:
			for attr in 'size used allocated'.split():
				r[attr] = int(r[attr])
			r.free = r.size - r.used - r.allocated
			if r.size == 0:
				r.percent = 0.0
			else:
				r.percent = 100.0 * (r.used + r.allocated) / r.size
		return res

	def linkgroups(self):
		return self._parsesrm_startingwith('Reservations:')

	def _parsesrm_startingwith(self, starttoken):
		collection = []
		srm = dcachecmd('cd SrmSpaceManager', 'ls -l')
		parser = SrmParser()

		ready = False
		for line in srm:
			line = line.strip()
			if ready and line == '':
				break
			if ready:
				try:
					collection.append(parser.parse(line))
				except InvalidSrmNotationError:
					# end of the list
					break
			if line.startswith(starttoken):
				ready = True

		srm.close()
		return collection
