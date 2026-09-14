# -*- coding: utf-8 -*-

from navis_ui import show_form, show_options_form
from tools.navis_batch import BatchNavisViewWorkflow

# ==========================================================
# START
# ==========================================================

if __shiftclick__:
    show_options_form()
    raise SystemExit


settings = show_form()

if settings:
    BatchNavisViewWorkflow(__revit__.Application).run(settings)
