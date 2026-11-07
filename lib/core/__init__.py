# extension library file

import os.path as op
from System import Version

VERSION_URL = 'https://raw.githubusercontent.com/romangolev/pyArchitect/main/lib/core/version'


def get_local_version():
    with open(op.join(op.dirname(__file__), 'version'), 'r') as version_file:
       version = version_file.read()
    return version

# Get version inside the github repository
def get_git_version(timeout=3):
   try:
      import urllib2
   except ImportError:
      import urllib.request as urllib2
   text = urllib2.urlopen(VERSION_URL, timeout=timeout).read()
   if not isinstance(text, str):
      text = text.decode('utf-8')
   return text.strip()

def newer_version():
   """Return the version on GitHub when it is newer than this one, else None."""
   try:
      remote = get_git_version()
      if Version(remote) > Version(get_local_version()):
         return remote
   except Exception:
      pass
   return None
