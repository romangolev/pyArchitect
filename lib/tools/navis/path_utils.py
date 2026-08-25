# -*- coding: utf-8 -*-


def get_file_name(path):

    if not path:
        return ""

    return (
        path
        .replace("\\", "/")
        .split("/")[-1]
    )


def is_server_path(path):

    return path.upper().startswith(
        "RSN://"
    )