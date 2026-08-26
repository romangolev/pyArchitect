# -*- coding: utf-8 -*-

from tools.model_finder import find_rvt_files


class LocalModelFinder(object):
    """Finds Revit models from a local-folder batch source."""

    def find(self, settings):
        folder = settings.get("models_folder", "")

        recursive = settings.get("recursive", True)

        if not folder:
            return []

        return find_rvt_files(folder, recursive)
