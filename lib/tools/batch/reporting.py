# -*- coding: utf-8 -*-
"""Shared rendering and persistence helpers for batch-command results."""

from tools.batch.strings import S
from tools.reporting import ActivityReport


def print_result_report(
    output, title, rows, columns, success_values=("OK",), status_index=-1
):
    success_count = sum(1 for row in rows if row[status_index] in success_values)
    failure_count = len(rows) - success_count
    output.print_md("## {}".format(title))
    output.print_md(S("report.summary", success_count, failure_count))
    output.print_table(table_data=rows, columns=columns)


def save_batch_report(tool_name, rows, columns):
    """Persist batch results using the extension-wide reporting facility."""
    report = ActivityReport(tool_name, columns)
    for row in rows:
        report.add(*row)
    return report.save()


def save_report_copy(report, folder=None, label=None):
    """Write a report to disk, reporting success or failure to the output."""
    label = label or S("report.label.report")
    try:
        path = report.save(folder)
        print(S("report.saved", label, path))
        return path
    except Exception as exception:
        print(S("report.save_failed", label, exception))
        return None
