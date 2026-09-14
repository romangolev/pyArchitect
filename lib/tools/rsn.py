# -*- coding: utf-8 -*-


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


class RsnModelListReader(object):
    """Parses Revit Server model lists from free-form text."""

    def parse(self, text):
        models = []
        seen = set()

        for line in (text or "").splitlines():
            path = normalize_rsn_path(line)
            if not path:
                continue

            key = path.upper()
            if key in seen:
                continue

            seen.add(key)
            models.append(path)

        return models
