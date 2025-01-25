import Autodesk.Revit.DB as DB
from core.warningsuppressor import WarningSuppressor

class WrappedTransaction:
    """
    This class is a wrapper for the Revit Transaction class.
    It is used to simplify the transaction

    Example:
    with WrappedTransaction(doc, "My beautiful transaction") as t:
        # Do something
    """
    def __init__(self, doc, name="My beautiful transaction", warning_suppressor=False):
        self.doc = doc                                  # type: DB.Document 
        self.name = name                                # type: str
        self.transaction = DB.Transaction(doc, name)    # type: DB.Transaction
        # Set optional warning suppressor
        if warning_suppressor is not False:
            options = self.transaction.GetFailureHandlingOptions()
            options.SetFailuresPreprocessor(WarningSuppressor())
            self.transaction.SetFailureHandlingOptions(options)

    def __enter__(self):
        self.transaction.Start()
        return self

    def __exit__(self, ex_type, ex_value, ex_traceback):
        if ex_type is None:
            self.transaction.Commit()
        else:
            self.transaction.RollBack()
            print(ex_type, ex_value, ex_traceback)

class WrappedTransactionGroup:
    """
    This class is a wrapper for the Revit TransactionGroup class.
    It is used to simplify the transaction group
    
    Example:
    with WrappedTransactionGroup(doc, "My beautiful transaction group") as transaction_group:
        # Do something
    """
    def __init__(self, doc, name="My beautiful transaction group"):
        self.doc = doc                                          # type: DB.Document 
        self.name = name                                        # type: str
        self.transaction_group = DB.TransactionGroup(doc, name) # type: DB.TransactionGroup

    def __enter__(self):
        self.transaction_group.Start()
        return self

    def __exit__(self, ex_type, ex_value, ex_traceback):
        if ex_type is None:
            self.transaction_group.Assimilate()
        else:
            self.transaction_group.RollBack()
            print(ex_type, ex_value, ex_traceback)