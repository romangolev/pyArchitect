# -*- coding: utf-8 -*-

from local_finder import find_local_models
from rsn_reader import parse_model_list


def get_models(settings):

    source = settings.get(
        "source",
        "LOCAL"
    ).upper()

    if source == "LOCAL":

        return find_local_models(
            settings
        )

    if source == "RSN":

        return parse_model_list(

            settings.get(
                "server_models",
                ""
            )

        )

    return []