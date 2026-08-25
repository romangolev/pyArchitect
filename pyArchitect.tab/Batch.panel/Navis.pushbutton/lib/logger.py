# -*- coding: utf-8 -*-

from datetime import datetime

from tools.reporting import ActivityReport


class Logger(object):

    def __init__(self):

        self.report = ActivityReport(
            "BatchNavisViews",
            ["DateTime", "Result", "FileName", "FilePath", "Comment"])

    def add(
            self,
            file_path,
            result,
            comment=""
    ):

        file_name = os.path.basename(
            file_path
        )

        self.report.add(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            result,
            file_name,
            file_path,
            comment)

    def save(
            self,
            log_folder=None
    ):
        return self.report.save(log_folder)
