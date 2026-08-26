# -*- coding: utf-8 -*-

from pyrevit import script

from tools.batch.input import BatchInputItem
from tools.batch.processor import BatchProcessor
from tools.navis.batch_operation import NavisViewBatchOperation
from tools.reporting import BatchOperationReport
from tools.revit_documents import RevitDocumentRepository


class BatchNavisViewWorkflow(object):
    def __init__(self, application):
        self.application = application

    def run(self, settings):
        models = self._create_models(settings)
        if not models:
            print("No models selected.")
            return []

        operation = NavisViewBatchOperation()
        report = BatchOperationReport(operation.operation_id)
        processor = BatchProcessor(
            RevitDocumentRepository(self.application),
            report,
        )

        results = processor.run(
            [operation],
            models,
            settings.get("analysis_only", False),
            settings.get("upgrade_models", False),
        )

        self._print_summary(operation, results, settings.get("analysis_only", False))
        self._save_reports(report, settings)
        return results

    @staticmethod
    def _create_models(settings):
        hidden_worksets = settings.get("hidden_worksets", [])
        return [
            BatchInputItem(
                item["path"],
                {
                    "profile": item.get("profile", "UNIVERSAL"),
                    "hidden_worksets": hidden_worksets,
                },
            )
            for item in settings.get("selected_models", [])
        ]

    @staticmethod
    def _print_summary(operation, results, analysis_only):
        output = script.get_output()
        output.print_md("# {} batch processor".format(operation.display_name))
        output.print_table(
            table_data=[
                (
                    model.source_path,
                    operation.display_name,
                    result.status,
                    result.message,
                )
                for model, operation_results in results
                for operation, result in operation_results
            ],
            columns=["Model", "Operation", "Result", "Details"],
        )

        mode = "analysis" if analysis_only else "execution"
        print("{} completed for {} model(s).".format(mode.capitalize(), len(results)))

    @staticmethod
    def _save_reports(report, settings):
        try:
            report_path = report.save()
            print("REPORT SAVED: {}".format(report_path))
        except Exception as exception:
            print("REPORT ERROR: {}".format(exception))

        if settings.get("create_log", False):
            folder = settings.get("log_folder", "").strip()
            if not folder:
                print("LOG FOLDER NOT SPECIFIED")
                return

            try:
                log_path = report.save(folder)
                print("LOG SAVED: {}".format(log_path))
            except Exception as exception:
                print("LOG ERROR: {}".format(exception))
