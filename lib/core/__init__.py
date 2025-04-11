# extension library file

import os.path as op
from System import Version

class Core(object):
   """
   Extension Coreclass
   """
   @staticmethod
   def return_ext_dir():
      A_EXT_DIR = op.dirname(op.dirname(__file__))
      return A_EXT_DIR

def get_local_version():
    with open(op.join(op.dirname(__file__), 'version'), 'r') as version_file:
       version = version_file.read()
    return version

# Get version inside the github repository
def get_git_version():
   try:
      import urllib2
   except ImportError:
      import urllib.request as urllib2
   data = urllib2.urlopen('https://raw.githubusercontent.com/romangolev/pyArchitect/main/lib/core/version')
   for line in data: 
      gitversion = line
   return gitversion

def update_needed():
   try:
      if Version(get_local_version()) < Version(get_git_version()):
         return True
      else:
         return False
   except Exception:
      return False
