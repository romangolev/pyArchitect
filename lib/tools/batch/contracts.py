# -*- coding: utf-8 -*-


class BatchOperationResult(object):
    def __init__(self, status, message="", changed=False):
        self.status = status
        self.message = message
        self.changed = changed


class BatchOperationContext(object):
    def __init__(self, document, model, opened_by_processor):
        self.document = document
        self.model = model
        self.opened_by_processor = opened_by_processor


class BatchOperation(object):
    operation_id = None
    display_name = None

    def analyze(self, context):
        raise NotImplementedError

    def execute(self, context):
        raise NotImplementedError
