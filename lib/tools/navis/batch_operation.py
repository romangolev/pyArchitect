# -*- coding: utf-8 -*-

from tools.batch.contracts import BatchOperation, BatchOperationResult
from tools.navis.navis_view import (
    create_or_replace_navisworks_view,
    has_navisworks_view,
)


class NavisViewBatchOperation(BatchOperation):
    operation_id = "navis-view"
    display_name = "Navisworks view"

    def analyze(self, context):
        if has_navisworks_view(context.document):
            return BatchOperationResult("EXISTS", "Navisworks view exists")

        return BatchOperationResult("MISSING", "Navisworks view not found")

    def execute(self, context):
        profile = context.model.options.get("profile", "UNIVERSAL")
        hidden_worksets = context.model.options.get("hidden_worksets", [])
        status = create_or_replace_navisworks_view(
            context.document,
            profile,
            hidden_worksets,
            recreate=context.opened_by_processor,
        )
        return BatchOperationResult(status, changed=True)
