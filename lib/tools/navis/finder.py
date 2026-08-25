# -*- coding: utf-8 -*-

import os
import re


def is_backup_file(file_name):

    return re.match(
        r".+\.\d{4}\.rvt$",
        file_name,
        re.IGNORECASE
    ) is not None


def find_rvt_files(
        folder,
        recursive=True):

    rvt_files = []

    if recursive:

        for root, dirs, files in os.walk(folder):

            for file_name in files:

                if not file_name.lower().endswith(
                        ".rvt"):

                    continue

                if is_backup_file(
                        file_name):

                    continue

                rvt_files.append(

                    os.path.join(
                        root,
                        file_name
                    )
                )

    else:

        for file_name in os.listdir(folder):

            full_path = os.path.join(
                folder,
                file_name
            )

            if not os.path.isfile(
                    full_path):

                continue

            if not file_name.lower().endswith(
                    ".rvt"):

                continue

            if is_backup_file(
                    file_name):

                continue

            rvt_files.append(
                full_path
            )

    return sorted(rvt_files)