# -*- coding: utf-8 -*-

from navis_ui import show_form
from tools.navis.settings import configure
from tools.navis_batch import BatchNavisViewWorkflow


def main():
    models, settings = show_form()
    if settings:
        BatchNavisViewWorkflow(__revit__.Application).run(models, settings)


if __name__ == "__main__":
    if __shiftclick__:
        configure()
    else:
        main()
