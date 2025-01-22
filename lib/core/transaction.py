import Autodesk.Revit.DB as DB
import traceback

class WrappedTransaction:
    """
    This class is a wrapper for the Revit Transaction class.
    It is used to simplify the transaction

    Example:
    with WrappedTransaction(doc, "My beautiful transaction") as t:
        # Do something
    """
    def __init__(self, doc, name="My beautiful transaction"):
        self.doc = doc # type: DB.Document 
        self.name = name # type: str
        self.transaction = DB.Transaction(doc, name) # type: DB.Transaction

    def __enter__(self):
        self.transaction.Start()
        return self

    def __exit__(self, ex_type):
        if ex_type is None:
            try:
                self.transaction.Commit()
                return True
            except Exception as exception:
                self.transaction.RollBack()
                print(traceback.format_exc())
                raise exception
        elif ex_type:
            self.transaction.RollBack()
            raise ex_type

class WrappedTransactionGroup:
    """
    This class is a wrapper for the Revit TransactionGroup class.
    It is used to simplify the transaction group
    
    Example:
    with WrappedTransactionGroup(doc, "My beautiful transaction group") as transaction_group:
        # Do something
    """
    def __init__(self, doc, name="My beautiful transaction group"):
        self.doc = doc # type: DB.Document 
        self.name = name # type: str
        self.transaction_group = DB.TransactionGroup(doc, name) # type: DB.TransactionGroup

    def __enter__(self):
        self.transaction_group.Start()
        return self

    def __exit__(self, ex_type):
        if ex_type is None:
            try:
                self.transaction_group.Assimilate()
                return True
            except Exception as exception:
                self.transaction_group.RollBack()
                print(traceback.format_exc())
                raise exception
        elif ex_type:
            self.transaction.RollBack()
            raise ex_type            