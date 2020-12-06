# Blank architects extension library file
# 
#
#
#
import os
import sys
import os.path as op

def get_version():
    with open(op.join(op.dirname(__file__), 'version'), 'r') as version_file:
       BA_version = version_file.read()
    return BA_version