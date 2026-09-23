# -*- coding: utf-8 -*-

import os

from pyrevit import script

from tools.batch.processor import BatchProcessor
from tools.batch.strings import S
from tools.navis.batch_operation import NavisViewBatchOperation
from tools.revit_documents import RevitDocumentRepository


SUCCESS_VALUES = ("CREATED", "UPDATED", "EXISTS", "MISSING")


class BatchNavisViewWorkflow(object):
    def __init__(self, application):
        self.application = application

    def run(self, models, settings):
        if not models:
            print(S("navis.run.no_models"))
            return []

        save_mode = settings.get("save_mode")
        if save_mode not in ("copy_output", "edit_sources"):
            print(S("navis.run.no_save_mode"))
            return []
        copy_destination = None
        if save_mode == "copy_output":
            copy_destination = settings.get("copy_destination", "").strip()
            if not copy_destination or not os.path.isdir(copy_destination):
                print(S("navis.run.no_output_folder"))
                return []

        analysis_only = settings.get("analysis_only", False)
        operation = NavisViewBatchOperation(settings.get("hidden_worksets", []))
        processor = BatchProcessor(RevitDocumentRepository(self.application))
        logger = script.get_logger()
        logger.debug("Starting Navis batch for %s model(s)", len(models))

        results = processor.run(
            [operation],
            models,
            analysis_only,
            settings.get("upgrade_models", False),
            copy_destination,
        )

        output = script.get_output()
        self._print_summary(output, logger, operation, results, analysis_only)
        return results

    @staticmethod
    def _print_summary(output, logger, operation, results, analysis_only):
        rows = [
            (model.source_path, ran.display_name, result.status, result.message)
            for model, operation_results in results
            for ran, result in operation_results
        ]
        output.print_md("## {}".format(S("navis.run.results_title", operation.display_name)))
        output.print_table(
            table_data=rows,
            columns=[
                S("navis.column.model"),
                S("navis.column.operation"),
                S("navis.column.result"),
                S("navis.column.details"),
            ],
        )
        for row in rows:
            if row[2] not in SUCCESS_VALUES:
                logger.warning(u"{}: {}".format(row[0], row[3]))

        mode = S(
            "navis.run.mode.analysis" if analysis_only else "navis.run.mode.execution"
        )
        logger.info(S("navis.run.completed", mode, len(results)))
