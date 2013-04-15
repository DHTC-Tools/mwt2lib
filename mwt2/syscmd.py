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


class spawn(object):
	'''Spawn creates a child process.  A function and arguments are passed
	to the initializer.  The parent returns a spawn instance which can be
	used to manipulate the child by sending and receiving stdio.  The child
	immediately begins executing the function, called with the specified
	arguments and keywords, then exits.

	Example:
	def identify(name, flags=None):
		import os
		print 'I am', name
		print 'PID =', os.getpid()
		print 'Flags =', flags

	s = spawn(identify, 'demo', flags=6)
	for line in s:
		print 'Child says:', line.strip()
	'''

	import os
	import sys
	import unbuffered

	def __init__(self, function, *args, **kwargs):
		fromparent, tochild = self.os.pipe()
		fromchild, toparent = self.os.pipe()

		self.childpid = self.os.fork()
		if self.childpid == 0:
			# child
			self.os.close(tochild)
			self.os.close(fromchild)
			self.os.dup2(fromparent, 0)
			self.os.dup2(toparent, 1)
			# n.b. stderr is shared

			self.sys.exit(function(*args, **kwargs))

		self.os.close(fromparent)
		self.os.close(toparent)
		self.readfd = fromchild
		self.writefd = tochild
		self.readfp = self.os.fdopen(self.readfd, 'r')
		self.writefp = self.os.fdopen(self.writefd, 'w')


	def read(self, sz):
		return self.readfp.read(sz)


	def write(self, msg):
		return self.writefp.write(msg)


	def flush(self):
		self.writefp.flush()


	def readline(self):
		return self.readfp.readline()


	def readlines(self):
		return self.readfp.readlines()


	def __iter__(self):
		return self.readfp.__iter__()


	def close(self):
		self.readfp.close()
		self.writefp.close()
		self.os.close(self.readfd)
		self.os.close(self.writefd)
		self.os.kill(self.childpid)


	def wait(self):
		os.waitpid(self.childpid, 0)


class breeder(list):
	'''Container for spawned subprocesses.  Breeder's .spawn() method works
	the same as the spawn class's constructor, but adds the child to the
	breeder.  The caller can iterate on the breeder (or use any other list
	behavior), and can call breeder.waitall() to wait on all children.

	Example:
	def identify(name, flags=None):
		import os
		print 'I am', name
		print 'PID =', os.getpid()
		print 'Flags =', flags

	b = breeder()
	for i in xrange(1, 6):
		s = b.spawn(identify, 'demo%d' % i, flags=6)
		print os.getpid()
		for line in s:
			print '>>', line.strip()

	print b
	b.waitall()
	print b
	'''

	def spawn(self, function, *args, **kwargs):
		'''Create a spawn instance as a member of the breeder.'''
		s = spawn(function, *args, **kwargs)
		self.append(s)
		return s


	def waitall(self):
		'''Wait on all member children.'''
		x = list(self)
		for s in x:
			s.wait()
			self.remove(s)
