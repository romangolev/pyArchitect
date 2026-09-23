# -*- coding: utf-8 -*-

import os
import shutil

from tools.batch.contracts import BatchOperationContext, BatchOperationResult
from tools.batch.strings import S
from tools.export.persistence import save_sync_and_relinquish


SKIPPED = "SKIPPED"
ERROR = "ERROR"


class BatchProcessor(object):
    def __init__(self, document_repository):
        self.document_repository = document_repository

    def run(
        self,
        operations,
        models,
        analysis_only=False,
        upgrade_models=False,
        copy_destination=None,
    ):
        operations = self._as_operations(operations)
        results = []

        for model in models:
            operation_results = self._run_model(
                operations,
                model,
                analysis_only,
                upgrade_models,
                copy_destination,
            )
            results.append((model, operation_results))

        return results

    @staticmethod
    def _as_operations(operations):
        if isinstance(operations, (list, tuple)):
            return operations
        return [operations]

    def _run_model(
        self, operations, model, analysis_only, upgrade_models, copy_destination
    ):
        if (
            self.document_repository.requires_upgrade(model.source_path)
            and not upgrade_models
        ):
            return [
                (
                    operation,
                    BatchOperationResult(SKIPPED, S("processor.requires_upgrade")),
                )
                for operation in operations
            ]

        document = None
        should_close = False
        processed_path = model.source_path

        try:
            # Copy only for a real run. Analysis must remain read-only even
            # when the caller configured an output destination.
            if copy_destination and not analysis_only:
                processed_path = self._copy_model(model.source_path, copy_destination)
            document, should_close = self.document_repository.open(processed_path)
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
                if copy_destination:
                    # A copied workshared model can still retain a reference
                    # to its source central.  Saving locally is deliberate:
                    # never synchronize a Navis-copy run back to that source.
                    document.Save()
                else:
                    save_sync_and_relinquish(document, "Batch operation pipeline")

            if copy_destination and not analysis_only:
                for _, result in results:
                    result.message = "{} {}".format(
                        result.message, S("processor.saved_copy", processed_path)
                    ).strip()

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

    @staticmethod
    def _copy_model(source_path, destination):
        """Make a non-overwriting RVT copy which is safe for a batch edit."""
        if source_path.strip().upper().startswith("RSN://"):
            raise ValueError(S("processor.rsn_not_copyable"))
        if not os.path.isdir(destination):
            raise ValueError(S("processor.destination_missing", destination))

        target_path = os.path.join(destination, os.path.basename(source_path))
        source_key = os.path.normcase(os.path.abspath(source_path))
        target_key = os.path.normcase(os.path.abspath(target_path))
        if source_key == target_key:
            raise ValueError(S("processor.same_folder"))
        if os.path.exists(target_path):
            raise ValueError(S("processor.copy_exists", target_path))

        shutil.copy2(source_path, target_path)
        return target_path
