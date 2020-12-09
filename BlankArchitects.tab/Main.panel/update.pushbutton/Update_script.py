# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__context__ = 'zero-doc'

import os
#from rpm.system.ui import UI
#from pyrevit.coreutils.ribbon import ICON_LARGE
from pyrevit import versionmgr
import blank
from pyrevit.versionmgr import updater
from pyrevit.coreutils import git
from pyrevit import forms
import urllib2

from pyrevit.coreutils import ribbon
from pyrevit.versionmgr import updater
from pyrevit.userconfig import user_config
from pyrevit import script

# Get installed version
blankinstalledversion = blank.get_version()

# Get versiob inside the github repository
data = urllib2.urlopen('https://raw.githubusercontent.com/BlankArchitects/pyBlank/main/lib/blank/version')
for line in data: 
	blankgitversion = line


def __selfinit__(script_cmp, ui_button_cmp, __rvt__):
	try:
		has_update_icon = script_cmp.get_bundle_file('icon-hasupdates.png')
		if blankgitversion != blankinstalledversion :
			ui_button_cmp.set_icon(has_update_icon,
                                   icon_size=ribbon.ICON_LARGE)
	except:
		0




if blankgitversion == blankinstalledversion :
	notification = forms.alert(  'Установлена последняя версия расширения\n'
								'BlankArchitects for Revit\n',
								ok=False, yes=True, no=True)
	print True

else:
	#updater.repo()
	print False