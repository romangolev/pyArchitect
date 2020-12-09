# Blank architects extension library file
# 
#
#
#
import os
import sys
import os.path as op


from pyrevit import EXEC_PARAMS
from pyrevit import script
from pyrevit import forms
from pyrevit.loader import sessionmgr
from pyrevit.loader import sessioninfo

def get_version():
    with open(op.join(op.dirname(__file__), 'version'), 'r') as version_file:
       BA_version = version_file.read()
    return BA_version

def start_reload():
   logger = script.get_logger()
   results = script.get_results()
   
   # re-load pyrevit session.
   logger.info('Reloading....')
   sessionmgr.reload_pyrevit()
   results.newsession = sessioninfo.get_session_uuid()