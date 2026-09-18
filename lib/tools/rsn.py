# -*- coding: utf-8 -*-

import re


DRIVE_LETTER = re.compile(r"^[A-Za-z]:$")


def normalize_rsn_path(path):
    """Return a canonical ``RSN://host/path`` route, or None if it is not one.

    Accepts a route that already carries the scheme, in either slash style, and
    a bare ``host/path`` whose first segment looks like a host name.  A local
    path is rejected rather than coerced: a drive letter would otherwise pass
    the host test on its colon and turn ``C:\\M.rvt`` into ``RSN://C:/M.rvt``.
    """
    path = path.strip().replace("\\", "/")

    if not path:
        return None

    if path.upper().startswith("RSN://"):
        while "//" in path[6:]:
            path = path[:6] + path[6:].replace("//", "/")

        return path

    parts = path.split("/")

    if len(parts) < 2:
        return None

    server = parts[0].strip()

    if DRIVE_LETTER.match(server):
        return None

    if server.upper().rstrip(":") == "RSN":
        return None

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
