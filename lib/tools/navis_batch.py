# -*- coding: utf-8 -*-

from pyrevit import script

from tools.batch.processor import BatchProcessor
from tools.batch.reporting import print_result_report, save_report_copy
from tools.navis.batch_operation import NavisViewBatchOperation
from tools.reporting import BatchOperationReport
from tools.revit_documents import RevitDocumentRepository


COLUMNS = ["Model", "Operation", "Result", "Details"]
SUCCESS_VALUES = ("CREATED", "UPDATED", "EXISTS", "MISSING")


class BatchNavisViewWorkflow(object):
    def __init__(self, application):
        self.application = application

    def run(self, models, settings):
        if not models:
            print("No models selected.")
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
            "{} batch processor".format(operation.display_name),
            rows,
            COLUMNS,
            SUCCESS_VALUES,
            status_index=2,
        )

        mode = "Analysis" if analysis_only else "Execution"
        print("{} completed for {} model(s).".format(mode, len(results)))

    @staticmethod
    def _save_reports(report, settings):
        save_report_copy(report)

        if not settings.get("create_log", False):
            return

        folder = settings.get("log_folder", "").strip()
        if not folder:
            print("LOG FOLDER NOT SPECIFIED")
            return

        save_report_copy(report, folder, "LOG")
