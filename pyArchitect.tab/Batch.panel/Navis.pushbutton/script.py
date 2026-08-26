# -*- coding: utf-8 -*-

from navis_ui import show_form
from tools.navis.settings import configure
from tools.navis_batch import BatchNavisViewWorkflow

# ==========================================================
# START
# ==========================================================

if __shiftclick__:
    configure()
    raise SystemExit


settings = show_form()

if settings:

    BatchNavisViewWorkflow(__revit__.Application).run(settings)
