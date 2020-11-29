#
#
#
import pyrevit
from pyrevit import forms
from pyrevit import HOST_APP


print(forms.toaster.get_toaster())
forms.toaster.send_toast("Hello World")