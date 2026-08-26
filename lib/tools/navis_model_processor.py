# -*- coding: utf-8 -*-

from tools.navis.navis_view import (
    has_navisworks_view,
    create_or_replace_navisworks_view,
)

from tools.revit_documents import open_document, requires_upgrade
from tools.export.persistence import save_sync_and_relinquish

from tools.navis_batch_statuses import CREATED, UPDATED, EXISTS, MISSING, SKIPPED, ERROR


def process_model(
    app, file_path, profile, analysis_only, upgrade_models, hidden_worksets, logger
):

    doc = None

    should_close = False

    try:
        if requires_upgrade(file_path) and not upgrade_models:
            print("SKIPPED - REQUIRES UPGRADE")

            logger.add(file_path, SKIPPED, "Model requires upgrade")

            return SKIPPED

        doc, should_close = open_document(app, file_path)

        if should_close:
            print("DOCUMENT: Opened by script")

        else:
            print("DOCUMENT: Already opened")

        if analysis_only:
            if has_navisworks_view(doc):
                logger.add(file_path, EXISTS)

                print("NAVISWORKS VIEW EXISTS")

                return EXISTS

            logger.add(file_path, MISSING)

            print("NAVISWORKS VIEW NOT FOUND")

            return MISSING

        status = create_or_replace_navisworks_view(
            doc, profile, hidden_worksets, recreate=should_close
        )

        save_sync_and_relinquish(doc, "Batch Navisworks view update")

        logger.add(file_path, status)

        print(status)

        return status

    except Exception as ex:
        logger.add(file_path, ERROR, str(ex))

        print("")
        print("ERROR")
        print(str(ex))

        return ERROR

    finally:
        if should_close and doc:
            try:
                doc.Close(False)

            except:
                pass


class ModelProcessor(object):
    """Application service for processing one Revit model at a time."""

    def __init__(self, application, logger):
        self.application = application
        self.logger = logger

    def process(
        self, file_path, profile, analysis_only, upgrade_models, hidden_worksets
    ):
        return process_model(
            self.application,
            file_path,
            profile,
            analysis_only,
            upgrade_models,
            hidden_worksets,
            self.logger,
        )
