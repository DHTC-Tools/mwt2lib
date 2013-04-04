# standard
import os

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
