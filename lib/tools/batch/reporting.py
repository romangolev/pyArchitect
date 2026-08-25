# -*- coding: utf-8 -*-
"""Shared rendering helpers for batch-command results."""


def print_result_report(output, title, results, columns, success_value="OK"):
    success_count = sum(1 for result in results if result[-1] == success_value)
    failure_count = len(results) - success_count
    output.print_md("## {}".format(title))
    output.print_md("**{} succeeded, {} failed/skipped**".format(
        success_count,
        failure_count))
    output.print_table(table_data=results, columns=columns)
