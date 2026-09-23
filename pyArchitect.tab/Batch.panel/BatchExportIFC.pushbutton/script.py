# -*- coding: utf-8 -*-
"""Batch IFC command controller.

The command owns user interaction and orchestration only. Reusable Revit
document and IFC export behaviour lives in ``tools.batch``.
"""

import os

from pyrevit import forms, script

from ifc_ui import show_form, show_options_form
from tools.batch.ifc import IFCBatchExporter
from tools.batch.strings import S


__helpurl__ = ""


def main():
    selected, settings = show_form()
    if not settings:
        return

    logger = script.get_logger()
    logger.debug("Starting IFC batch export for %s model(s)", len(selected))
    exporter = IFCBatchExporter(__revit__.Application, __revit__, logger)
    results = []
    with forms.ProgressBar(title=S("ifc.progress")) as progress_bar:
        for index, item in enumerate(selected):
            progress_bar.update_progress(index, len(selected))
            results.extend(exporter.export_item(item, settings))
        progress_bar.update_progress(len(selected), len(selected))

    output = script.get_output()
    output.print_md("## {}".format(S("ifc.results_title")))
    output.print_table(
        table_data=results,
        columns=[S("ifc.column.model"), S("ifc.column.view"), S("ifc.column.result")],
    )
    for model, view, result in results:
        if result != "OK":
            logger.warning(u"{} ({}): {}".format(model, view, result))
    logger.info(S("ifc.alert.finished", len(results)))

    if settings.open_folders:
        for folder in set(item.export_path for item in selected):
            try:
                os.startfile(folder)
            except Exception:
                pass

    forms.alert(
        S("ifc.alert.finished", len(results)),
        title=S("ifc.title"),
    )


if __name__ == "__main__":
    if __shiftclick__:
        show_options_form()
    else:
        main()
