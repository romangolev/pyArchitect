# -*- coding: utf-8 -*-
"""Persistence rules shared by all exports."""

import Autodesk.Revit.DB as DB


def save_sync_and_relinquish(document, comment):
    if document.IsWorkshared:
        transact_options = DB.TransactWithCentralOptions()
        relinquish_options = DB.RelinquishOptions(True)
        sync_options = DB.SynchronizeWithCentralOptions()
        sync_options.SetRelinquishOptions(relinquish_options)
        sync_options.Comment = comment
        document.SynchronizeWithCentral(transact_options, sync_options)
        DB.WorksharingUtils.RelinquishOwnership(
            document, relinquish_options, transact_options)
    else:
        document.Save()
