# extension library file

import os
import sys
import os.path as op
import urllib2
import selectionhelpers

from pyrevit import EXEC_PARAMS
from pyrevit import script
from pyrevit import forms
from pyrevit.loader import sessionmgr
from pyrevit.loader import sessioninfo

class Core :
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

def start_reload():
   logger = script.get_logger()
   results = script.get_results()
   
   # re-load pyrevit session.
   logger.info('Reloading....')
   sessionmgr.reload_pyrevit()
   results.newsession = sessioninfo.get_session_uuid()

# Get version inside the github repository
def get_git_version():
   data = urllib2.urlopen('https://raw.githubusercontent.com/romangolev/pyArchitect/main/lib/core/version')
   for line in data: 
      gitversion = line
   return gitversion

def update_needed():
   if get_local_version() != get_git_version():
      return True
   else:
      return False