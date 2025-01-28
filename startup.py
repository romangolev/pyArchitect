"""
              _          _    _ _          _   
  _ __ _  _  /_\  _ _ __| |_ (_) |_ ___ __| |_ 
 | '_ \ || |/ _ \| '_/ _| ' \| |  _/ -_) _|  _|
 | .__/\_, /_/ \_\_| \__|_||_|_|\__\___\__|\__|
 |_|   |__/                                    

"""
from pyrevit import forms
import core

# Toast notify for new updates
try:
    if core.update_needed() == True:
        forms.toaster.send_toast("New update for pyArchitect extension available: {}".format(core.get_git_version()))
    else:
        pass
except Exception:
    pass
