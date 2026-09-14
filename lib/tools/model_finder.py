# -*- coding: utf-8 -*-

import os
import re


BACKUP_PATTERN = re.compile(r".+\.\d{4}\.rvt$", re.IGNORECASE)


def is_backup_file(file_name):
    return BACKUP_PATTERN.match(file_name) is not None


def is_model_file(folder, file_name):
    if not file_name.lower().endswith(".rvt"):
        return False
    if is_backup_file(file_name):
        return False
    return os.path.isfile(os.path.join(folder, file_name))


def find_rvt_files(folder, recursive=True):
    walker = os.walk(folder) if recursive else [(folder, [], os.listdir(folder))]
    return sorted(
        os.path.join(root, file_name)
        for root, _, file_names in walker
        for file_name in file_names
        if is_model_file(root, file_name)
    )
