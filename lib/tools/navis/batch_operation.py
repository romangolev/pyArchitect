# -*- coding: utf-8 -*-
"""Navisworks view maintenance exposed as a batch operation."""

from core.transaction import WrappedTransaction
from tools.batch.contracts import BatchOperation, BatchOperationResult
from tools.batch.strings import S
from tools.navis.profiles import load_profiles
from tools.navis.settings import load as load_settings
from tools.navis.views import NavisworksViewService


class NavisViewBatchOperation(BatchOperation):
    operation_id = "navis-view"
    display_name = S("navis.operation.display_name")

    def __init__(self, hidden_worksets=None, settings=None, profiles=None):
        self.hidden_worksets = hidden_worksets or []
        self.settings = settings or load_settings()
        self.profiles = profiles or load_profiles()

    def service(self, document):
        return NavisworksViewService(document, self.settings, self.profiles)

    def analyze(self, context):
        if self.service(context.document).find() is not None:
            return BatchOperationResult("EXISTS", S("navis.operation.exists"))
        return BatchOperationResult("MISSING", S("navis.operation.missing"))

    def execute(self, context):
        profile = context.model.options.get("profile", self.settings.profile)
        recreate = self.settings.recreate_existing and context.opened_by_processor

        with WrappedTransaction(context.document, "Create or update Navisworks view"):
            _, status = self.service(context.document).reconcile(
                profile, self.hidden_worksets, recreate
            )

        return BatchOperationResult(status, changed=True)
