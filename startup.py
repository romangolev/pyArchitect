import pyrevit
from pyrevit import forms
from pyrevit import HOST_APP

import blank


# Toast notifier example
#TODO Notify user on update
#print(forms.toaster.get_toaster())
#forms.toaster.send_toast("Hello World")
if blank.update_needed() == True:
    forms.toaster.send_toast("New update for BlankArchitects extension available: {}".format(blank.get_git_version()))
else:
    pass