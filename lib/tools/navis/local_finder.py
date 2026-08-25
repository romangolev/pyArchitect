# -*- coding: utf-8 -*-

from finder import (
    find_rvt_files
)


# ==========================================================
# LOCAL MODELS
# ==========================================================

def find_local_models(settings):

    folder = settings.get(
        "models_folder",
        ""
    )

    recursive = settings.get(
        "recursive",
        True
    )

    if not folder:

        return []

    return find_rvt_files(
        folder,
        recursive
    )