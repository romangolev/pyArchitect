# -*- coding: utf-8 -*-

import os

from pyrevit import script

from tools.batch.processor import BatchProcessor
from tools.batch.reporting import print_result_report, save_report_copy
from tools.batch.strings import S
from tools.navis.batch_operation import NavisViewBatchOperation
from tools.reporting import BatchOperationReport
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
        report = BatchOperationReport(operation.operation_id)
        processor = BatchProcessor(
            RevitDocumentRepository(self.application),
            report,
        )

        results = processor.run(
            [operation],
            models,
            analysis_only,
            settings.get("upgrade_models", False),
            copy_destination,
        )

        self._print_summary(operation, results, analysis_only)
        self._save_reports(report, settings)
        return results

    @staticmethod
    def _print_summary(operation, results, analysis_only):
        rows = [
            (model.source_path, ran.display_name, result.status, result.message)
            for model, operation_results in results
            for ran, result in operation_results
        ]
        print_result_report(
            script.get_output(),
            S("navis.run.report_title", operation.display_name),
            rows,
            [
                S("navis.column.model"),
                S("navis.column.operation"),
                S("navis.column.result"),
                S("navis.column.details"),
            ],
            SUCCESS_VALUES,
            status_index=2,
        )

        mode = S(
            "navis.run.mode.analysis" if analysis_only else "navis.run.mode.execution"
        )
        print(S("navis.run.completed", mode, len(results)))

    @staticmethod
    def _save_reports(report, settings):
        save_report_copy(report)

        if not settings.get("create_log", False):
            return

        folder = settings.get("log_folder", "").strip()
        if not folder:
            print(S("navis.run.no_log_folder"))
            return

        save_report_copy(report, folder, S("report.label.log"))
