
'''Tools for platform discovery in the system running Python.
'''


class mounts(object):
	import os
	import re
	import platform

	class mount(object): pass

	def __init__(self, system=None):
		self.system = system or self.platform.system()

	def __iter__(self):
		for mpt, dev, type, opts in getattr(self, 'get_' + self.system)():
			# N.B. the dictionary comprehension is not valid in older pythons.
			opts = [opt.strip() for opt in opts.split(',')]
			simpleopts = [(opt, None) for opt in opts if '=' not in opt]
			kvopts = [opt.split('=', 1) for opt in opts if '=' in opt]
			opts = dict(simpleopts)
			opts.update(dict(kvopts))
			mount = self.mount()
			mount.mountpoint = mpt
			mount.dev = dev
			mount.type = type
			mount.opts = opts
			mount.stat = self.os.statvfs(mpt)
			yield mount

	# To port to a new platform, add a get_$(uname -s) function
	# that acts as an iterator returning (mpt, dev, type, opts)
	# tuples.  __iter__ above handles common work.

	def get_Linux(self):
		fp = open('/proc/mounts', 'r')
		lines = fp.readlines()
		fp.close()
		for line in lines:
			w = line.split()
			yield w[1], w[0], w[2], w[3]

	def get_Darwin(self):
		rx = self.re.compile('(.*) on ([^(]+) \((.*)\)')
		fp = self.os.popen('/sbin/mount', 'r')
		lines = fp.readlines()
		fp.close()
		for line in lines:
			m = rx.match(line)
			if not m:
				continue
			yield m.group(2), m.group(1), None, m.group(3)
