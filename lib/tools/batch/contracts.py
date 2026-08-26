# -*- coding: utf-8 -*-


class BatchOperationResult(object):
    def __init__(self, status, message="", changed=False):
        self.status = status
        self.message = message
        self.changed = changed


class BatchModelItem(object):
    def __init__(self, file_path, options=None):
        self.file_path = file_path
        self.options = options or {}


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


class BatchOperationRegistry(object):
    def __init__(self, operations=None):
        self._operations = {}
        for operation in operations or []:
            self.register(operation)

    def register(self, operation):
        if not operation.operation_id:
            raise ValueError("Batch operations require an operation_id")
        self._operations[operation.operation_id] = operation

    def get(self, operation_id):
        return self._operations[operation_id]

    def all(self):
        return self._operations.values()
