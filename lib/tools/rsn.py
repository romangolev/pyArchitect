# -*- coding: utf-8 -*-

import os


class RsnModelListReader(object):
    """Parses Revit Server model lists from text or CSV files."""

    def parse(self, text):
        return _parse_model_list(text)

    def read_csv(self, csv_file):
        return _load_csv(csv_file)


def _parse_model_list(text):

    models = []
    seen = set()

    for line in text.splitlines():
        line = normalize_rsn_path(line)

        if not line:
            continue

        key = line.upper()

        if key in seen:
            continue

        seen.add(key)

        models.append(line)

    return models


def _load_csv(csv_file):

    if not csv_file:
        return []

    if not os.path.exists(csv_file):
        return []

    try:
        import codecs

        with codecs.open(csv_file, "r", "utf-8-sig") as f:
            return _parse_model_list(f.read())

    except:
        pass

    try:
        with open(csv_file, "r") as f:
            return _parse_model_list(f.read())

    except:
        return []


def normalize_rsn_path(path):

    path = path.strip()

    if not path:
        return None

    if path.upper().startswith("RSN://"):
        path = path.replace("\\", "/")

        while "//" in path[6:]:
            path = path[:6] + path[6:].replace("//", "/")

        return path

    path = path.replace("\\", "/")

    parts = path.split("/")

    if len(parts) < 2:
        return None

    server = parts[0].strip()

    if "." not in server and ":" not in server:
        return None

    return "RSN://" + "/".join(parts)
