# -*- coding: utf-8 -*-
"""Batch IFC command controller.

The command owns user interaction and orchestration only. Reusable Revit
document and IFC export behaviour lives in ``tools.batch``.
"""

import os

from pyrevit import forms, script

from ifc_ui import ask_settings, collect_model_list, select_models
from tools.batch.ifc import IFCBatchExporter
from tools.batch.reporting import print_result_report


__helpurl__ = ""

XAML_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ui.xaml")


def main():
    items = collect_model_list()
    if not items:
        return

    selected = select_models(items)
    if not selected:
        return

    settings = ask_settings(XAML_FILE, len(selected))
    if not settings:
        return

    exporter = IFCBatchExporter(
        __revit__.Application,
        __revit__,
        script.get_logger())
    results = []
    with forms.ProgressBar(title="Exporting {value} of {max_value} models") as progress_bar:
        for index, item in enumerate(selected):
            progress_bar.update_progress(index, len(selected))
            results.extend(exporter.export_item(item, settings))
        progress_bar.update_progress(len(selected), len(selected))

    print_result_report(
        script.get_output(),
        "Batch IFC export report",
        results,
        ["Model", "View", "Result"])

    if settings.open_folders:
        for folder in set(item.export_path for item in selected):
            try:
                os.startfile(folder)
            except Exception:
                pass

    forms.alert(
        "{} export operation(s) finished.\nSee the pyRevit output window for the detailed report.".format(
            len(results)),
        title="Batch IFC Export")


if __name__ == "__main__":
    main()
