# -*- coding: utf-8 -*-

from tools.batch.contracts import BatchOperationContext, BatchOperationResult
from tools.export.persistence import save_sync_and_relinquish


SKIPPED = "SKIPPED"
ERROR = "ERROR"


class BatchProcessor(object):
    def __init__(self, document_repository, report):
        self.document_repository = document_repository
        self.report = report

    def run(self, operations, models, analysis_only=False, upgrade_models=False):
        operations = self._as_operations(operations)
        results = []

        for model in models:
            operation_results = self._run_model(
                operations,
                model,
                analysis_only,
                upgrade_models,
            )
            results.append((model, operation_results))
            for operation, result in operation_results:
                self.report.add(
                    model.file_path,
                    result.status,
                    "{}: {}".format(operation.operation_id, result.message),
                )

        return results

    @staticmethod
    def _as_operations(operations):
        if isinstance(operations, (list, tuple)):
            return operations
        return [operations]

    def _run_model(self, operations, model, analysis_only, upgrade_models):
        if (
            self.document_repository.requires_upgrade(model.file_path)
            and not upgrade_models
        ):
            return [
                (operation, BatchOperationResult(SKIPPED, "Model requires upgrade"))
                for operation in operations
            ]

        document = None
        should_close = False

        try:
            document, should_close = self.document_repository.open(model.file_path)
            context = BatchOperationContext(document, model, should_close)
            results = []
            changed = False

            for operation in operations:
                try:
                    result = (
                        operation.analyze(context)
                        if analysis_only
                        else operation.execute(context)
                    )
                except Exception as exception:
                    result = BatchOperationResult(ERROR, str(exception))
                results.append((operation, result))
                changed = changed or result.changed

            if changed:
                save_sync_and_relinquish(document, "Batch operation pipeline")

            return results

        except Exception as exception:
            return [
                (operation, BatchOperationResult(ERROR, str(exception)))
                for operation in operations
            ]

        finally:
            if should_close and document:
                try:
                    document.Close(False)
                except:
                    pass
