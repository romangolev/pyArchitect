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
version = core.newer_version()
if version:
    forms.toaster.send_toast("New update for pyArchitect extension available: {}".format(version))
