# -*- coding: utf-8 -*-
"""Export-report adapter over the extension-wide persistent reporter."""

from tools.reporting import ActivityReport


def save(tool_name, columns, rows):
    report = ActivityReport(tool_name, columns)
    for row in rows:
        report.add(*row)
    return report.save()
