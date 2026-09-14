# -*- coding: utf-8 -*-
"""Shared rendering and persistence helpers for batch-command results."""

from tools.reporting import ActivityReport


def print_result_report(
    output, title, rows, columns, success_values=("OK",), status_index=-1
):
    success_count = sum(1 for row in rows if row[status_index] in success_values)
    failure_count = len(rows) - success_count
    output.print_md("## {}".format(title))
    output.print_md(
        "**{} succeeded, {} failed/skipped**".format(success_count, failure_count)
    )
    output.print_table(table_data=rows, columns=columns)


def save_batch_report(tool_name, rows, columns):
    """Persist batch results using the extension-wide reporting facility."""
    report = ActivityReport(tool_name, columns)
    for row in rows:
        report.add(*row)
    return report.save()


def save_report_copy(report, folder=None, label="REPORT"):
    """Write a report to disk, reporting success or failure to the output."""
    try:
        path = report.save(folder)
        print("{} SAVED: {}".format(label, path))
        return path
    except Exception as exception:
        print("{} ERROR: {}".format(label, exception))
        return None
