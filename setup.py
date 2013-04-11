import sys
from setuptools import setup, find_packages

version = None

def versionHg():
	# mercurial's {latesttagdistance} is unavailable in some
	# semi-reasonable versions of mercurial, so we'll do it via the api.
	try:
		import mercurial
		from mercurial import ui, hg
		repo = hg.repository(ui.ui(), '.')
	except ImportError:
		return None
	except mercurial.error.RepoError:
		return None

	def latesttag(repo):
		tags = repo.tags().items()
		tags.sort(lambda a, b: -cmp(repo[a[1]].rev(), repo[b[1]].rev()))
		for tag, rev in tags:
			# detect 'v1.2.3' tags
			if tag.startswith('v') and tag[1] in '0123456789':
				distance = 1
				return tag, distance
		return None, 0

	tag, distance = latesttag(repo)
	if tag is None:
		return '0.0.dev.hg.' + repo['.'].hex()[:12]
	elif distance == 0:
		return tag
	else:
		return '%s.dev+%d' % (tag[1:], distance)

def versionGit():
	import os, re
	fp = os.popen('git describe --tags --match "v*"', 'r')
	line = fp.readline().strip()
	fp.close()
	rx = re.compile('^(.*)-(\d+)-g.......$')
	m = rx.search(line)
	# what does git describe show for a repo with no tags?
	if m:
		return '%s.dev+%s' % (m.group(1)[1:], m.group(2))
	else:
		return line

def versionUnknown():
	return '0.0.dev.unknown'

for finder in versionHg, versionGit, versionUnknown:
	version = finder()
	if version:
		break

setup(
	name = 'mwt2lib',
	version = version,
	author = 'US ATLAS Midwest Tier 2 Center',
	author_email = 'support@mwt2.org',
	license = 'MIT',
	packages = find_packages(),
)
