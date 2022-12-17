"""
import pyrevit
from pyrevit import forms
from pyrevit import HOST_APP

import core


# Toast notifier example
#TODO Notify user on update
#print(forms.toaster.get_toaster())
#forms.toaster.send_toast("Hello World")
if core.update_needed() == True:
    forms.toaster.send_toast("New update for pyArchitect extension available: {}".format(core.get_git_version()))
else:
    pass
"""