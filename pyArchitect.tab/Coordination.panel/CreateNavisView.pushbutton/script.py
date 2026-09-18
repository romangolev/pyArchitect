# -*- coding: utf-8 -*-
"""Create or update the configured Navisworks view in the active model."""

from core.transaction import WrappedTransaction
from tools.navis.settings import configure, load as load_settings
from tools.navis.views import NavisworksViewService


def main():
    if __shiftclick__:
        configure()
        return

    uidoc = __revit__.ActiveUIDocument
    document = uidoc.Document
    settings = load_settings()
    service = NavisworksViewService(document, settings)
    view = service.find()

    with WrappedTransaction(document, "Create or update Navisworks view"):
        if view is None:
            view = service.create(settings.profile)
        else:
            service.configure(view, settings.profile)

    uidoc.ActiveView = view


if __name__ == "__main__":
    main()
