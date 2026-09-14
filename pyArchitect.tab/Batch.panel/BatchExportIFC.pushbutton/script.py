# -*- coding: utf-8 -*-
"""Batch IFC command controller.

The command owns user interaction and orchestration only. Reusable Revit
document and IFC export behaviour lives in ``tools.batch``.
"""

import os

from pyrevit import forms, script

from ifc_ui import show_form, show_options_form
from tools.batch.ifc import IFCBatchExporter
from tools.batch.reporting import print_result_report, save_batch_report


__helpurl__ = ""


def main():
    selected, settings = show_form()
    if not settings:
        return

    exporter = IFCBatchExporter(__revit__.Application, __revit__, script.get_logger())
    results = []
    with forms.ProgressBar(
        title="Exporting {value} of {max_value} models"
    ) as progress_bar:
        for index, item in enumerate(selected):
            progress_bar.update_progress(index, len(selected))
            results.extend(exporter.export_item(item, settings))
        progress_bar.update_progress(len(selected), len(selected))

    print_result_report(
        script.get_output(),
        "Batch IFC export report",
        results,
        ["Model", "View", "Result"],
    )
    report_path = save_batch_report(
        "BatchIFCExport", results, ["Model", "View", "Result"]
    )

    if settings.open_folders:
        for folder in set(item.export_path for item in selected):
            try:
                os.startfile(folder)
            except Exception:
                pass

    forms.alert(
        "{} export operation(s) finished.\nReport saved to:\n{}".format(
            len(results), report_path
        ),
        title="Batch IFC Export",
    )


if __name__ == "__main__":
    if __shiftclick__:
        show_options_form()
    else:
        main()
