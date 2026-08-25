# -*- coding: utf-8 -*-

from tools.navis.ui import show_form
from tools.navis.settings import configure
from tools.navis.process_models import process_models

# ==========================================================
# START
# ==========================================================

if __shiftclick__:
    configure()
    raise SystemExit


settings = show_form()

if settings:

    process_models(
        settings
    )
