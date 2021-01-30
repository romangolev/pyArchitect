# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__doc__ = 'Обновляет плагин до последней версии.\n / \n Updates extension to the latest version in casse the update is applicable.'
__author__ = 'Roman Golev'
__title__ = "Обновить\nПлагин"
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

from pyrevit import EXEC_PARAMS
from pyrevit import script
from pyrevit import forms
from pyrevit.loader import sessionmgr
from pyrevit.loader import sessioninfo


from System.Diagnostics import Process
import os
import os.path as op

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

else:
	notification = forms.alert( 'Обнаружена новая версия расширения\n'
								'BlankArchitects for Revit\n'
								''
								'Для обновления необходимо продолжить\n'
								'Новая версия будет распакована\n'
								'приложение pyRevit перезапустится',
								ok=False, yes=True, no=True)
	if notification:
		parent = op.dirname
		bat_updater_location = parent(__file__) + r"\reload.bat"
		p = Process()
		p.StartInfo.UseShellExecute = False
		p.StartInfo.RedirectStandardOutput = False
		p.StartInfo.FileName = bat_updater_location
		p.Start()
		p.WaitForExit()

		logger = script.get_logger()
		results = script.get_results()
	
		# re-load pyrevit session.
		logger.info('Reloading....')
		sessionmgr.reload_pyrevit()
		results.newsession = sessioninfo.get_session_uuid()
	else:
		0

	#notification = forms.alert( 'После завершения распаковки\n'
	#							'необходимо перезапустить pyRevit\n',
	#							ok=False, yes=True, no=True)
	#updater.repo()