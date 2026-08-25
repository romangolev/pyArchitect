# -*- coding: utf-8 -*-

import os
import sys

# ==========================================================
# LIB
# ==========================================================

script_dir = os.path.dirname(__file__)

lib_dir = os.path.join(
    script_dir,
    "lib"
)

if lib_dir not in sys.path:

    sys.path.append(lib_dir)

# ==========================================================
# IMPORTS
# ==========================================================

from ui import show_form
from tools.navis.settings import configure

from process_models import (
    process_models
)

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
