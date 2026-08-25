# -*- coding: utf-8 -*-

import os

from pyrevit import script

from logger import Logger

from model_processor import (
    process_model
)

from document_loader import (

    is_workshared,

    is_central

)

from statuses import (

    CREATED,

    UPDATED,

    EXISTS,

    MISSING,

    SKIPPED,

    ERROR

)


def process_models(settings):

    source = settings.get(
        "source",
        "LOCAL"
    )

    if source == "LOCAL":

        if not settings.get(
                "models_folder",
                "").strip():

            print(
                "Не выбрана папка с моделями."
            )

            return

    elif source == "RSN":

        if not settings.get(
                "selected_models"):

            print(
                "Не выбрана ни одна модель Revit Server."
            )

            return

    else:

        print(
            "Неизвестный источник моделей."
        )

        return

    selected_models = settings[
        "selected_models"
    ]

    if not selected_models:

        print(
            "Не выбрано ни одной модели."
        )

        return

    analysis_only = settings[
        "analysis_only"
    ]

    upgrade_models = settings.get(
        "upgrade_models",
        False
    )

    hidden_worksets = settings.get(
        "hidden_worksets",
        []
    )   

    app = __revit__.Application

    output = script.get_output()

    logger = Logger()

    output.print_md(
        "# Navisworks View Creator"
    )

    output.print_md(
        "Выбрано моделей: {}".format(
            len(selected_models)
        )
    )

    print("")
    print("=" * 60)
    print("SETTINGS")
    print("=" * 60)

    print(
        "Recursive search: {}".format(
            settings["recursive"]
        )
    )

    print(
        "Analysis only: {}".format(
            analysis_only
        )
    )

    print(
        "Upgrade models: {}".format(
            upgrade_models
        )
    )

    print(
        "Selected files: {}".format(
            len(selected_models)
        )
    )

    print("")

    created_count = 0
    updated_count = 0

    exists_count = 0
    missing_count = 0

    skipped_count = 0

    error_count = 0

    for index, model in enumerate(
            selected_models):

        file_path = model[
            "path"
        ]
        print("")
        print("FILE PATH:")
        print(file_path)
        print("")
        profile = model[
            "profile"
        ]

        print("")
        print("=" * 60)

        print(
            "[{}/{}] {}".format(
                index + 1,
                len(selected_models),
                os.path.basename(
                    file_path
                )
            )
        )

        print(
            "PROFILE: {}".format(
                profile
            )
        )

        if is_central(file_path):

            print(
                "MODEL: Central"
            )

        elif is_workshared(file_path):

            print(
                "MODEL: Workshared"
            )

        else:

            print(
                "MODEL: Standalone"
            )

        status = process_model(

            app,

            file_path,

            profile,

            analysis_only,

            upgrade_models,

            hidden_worksets,
            
            logger

        )

        if status == CREATED:

            created_count += 1

        elif status == UPDATED:

            updated_count += 1

        elif status == EXISTS:

            exists_count += 1

        elif status == MISSING:

            missing_count += 1

        elif status == SKIPPED:

            skipped_count += 1

        elif status == ERROR:

            error_count += 1

    print("")
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if analysis_only:

        print(
            "EXISTS : {}".format(
                exists_count
            )
        )

        print(
            "MISSING : {}".format(
                missing_count
            )
        )

    else:

        print(
            "CREATED : {}".format(
                created_count
            )
        )

        print(
            "UPDATED : {}".format(
                updated_count
            )
        )

    print(
        "SKIPPED : {}".format(
            skipped_count
        )
    )

    print(
        "ERRORS : {}".format(
            error_count
        )
    )

    try:
        default_report_path = logger.save()
        print("REPORT SAVED: {}".format(default_report_path))
    except Exception as ex:
        print("REPORT ERROR: {}".format(ex))

    if settings["create_log"]:

        log_folder = settings.get(
            "log_folder",
            ""
        ).strip()

        if not log_folder:

            print("")
            print("LOG:")
            print("Папка для логов не указана.")

        else:

            try:
                log_path = logger.save(log_folder)

                print("")
                print("LOG SAVED:")
                print(log_path)

            except Exception as ex:

                print("")
                print("LOG ERROR:")
                print(str(ex))
