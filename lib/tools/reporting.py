# -*- coding: utf-8 -*-
"""Persistent, tool-agnostic execution reports for pyArchitect commands."""

import codecs
import os
import re
from datetime import datetime

from tools import config


DEFAULT_REPORT_FOLDER = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "pyRevit",
    "pyArchitect",
    "Reports",
)


class ActivityReport(object):
    """Collect result rows and persist a UTF-8 TSV report for any command."""

    def __init__(self, tool_name, columns):
        self.tool_name = tool_name
        self.columns = columns
        self.rows = []
        self.started_at = datetime.now()

    def add(self, *values):
        self.rows.append(tuple("" if value is None else value for value in values))

    @staticmethod
    def _safe_name(value):
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "report"

    @staticmethod
    def _tsv_value(value):
        return unicode(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")

    def save(self, folder=None):
        folder = folder or config.get_option("report_folder", DEFAULT_REPORT_FOLDER)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        timestamp = self.started_at.strftime("%Y%m%d-%H%M%S")
        filename = "{}-{}.tsv".format(self._safe_name(self.tool_name), timestamp)
        path = os.path.join(folder, filename)
        with codecs.open(path, "w", "utf-8") as report_file:
            report_file.write(
                "\t".join(self._tsv_value(value) for value in self.columns) + "\n"
            )
            for row in self.rows:
                report_file.write(
                    "\t".join(self._tsv_value(value) for value in row) + "\n"
                )
        return path


class BatchNavisReport(object):
    """Navis batch report backed by the extension-wide report implementation."""

    def __init__(self):
        self._report = ActivityReport(
            "BatchNavisViews", ["DateTime", "Result", "FileName", "FilePath", "Comment"]
        )

    def add(self, file_path, result, comment=""):
        self._report.add(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            result,
            os.path.basename(file_path),
            file_path,
            comment,
        )

    def save(self, folder=None):
        return self._report.save(folder)
