import os
import sys
import socket
import select
import fcntl

class shell(object):
	'''An unbuffered subshell.

	This launches a subprocess in a pseudo-tty (pty) so that output
	from the child can be unbuffered.  The shell object itself can
	return line-buffered outut via iteration, or arbitrary block
	output via read().
	'''

	def __init__(self, *args):
		rfd, wfd = os.openpty()

		self.child = os.fork()

		if self.child == 0:
			os.close(rfd)
			sys.stdout.close()
			os.dup2(wfd, 1)
			sys.stdout = os.fdopen(wfd)
			os.execvp(args[0], args)
			raise OSError, 'cannot exec %s' % args[0]

		os.close(wfd)
		self.poll = select.poll()
		self.poll.register(rfd, select.POLLIN)
		self.buffer = ''

	def __iter__(self):
		ready = True
		while ready:
			s = self._getdata()
			if s == None:
				return
			self.buffer += s
			lines = self.buffer.split('\n')
			self.buffer = lines.pop()
			for line in lines:
				yield line


	def _getdata(self):
		for fd, event in self.poll.poll():
			try:
				# os.read may return OSError on closed pty
				s = os.read(fd, 1024)
				if s == '':
					return None
			except OSError:
				ready = False
				return None

			return s

	def read(self):
		ready = True
		while ready:
			s = self._getdata()
			if s == None:
				return
			output = self.buffer + s
			self.buffer = ''
			return output

	def close(self):
		pass


if __name__ == '__main__':
	sh = shell(sys.argv[1:])
	for line in sh:
		sys.stdout.write('>> ' + line + '\n')
		sys.stdout.flush()
	sh.close()
