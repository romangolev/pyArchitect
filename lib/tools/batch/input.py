# -*- coding: utf-8 -*-

import codecs
import csv
import json
import os

from pyrevit import forms

from tools.local_models import LocalModelFinder
from tools.rsn import RsnModelListReader


class BatchInputItem(object):
    def __init__(self, source_path, options=None):
        self.source_path = source_path
        self.options = options or {}

    @property
    def name(self):
        return os.path.basename(self.source_path)


class BatchInput(object):
    def __init__(self, items=None):
        self.items = items or []

    def add(self, source_path, options=None):
        self.items.append(BatchInputItem(source_path, options))


class BatchInputFactory(object):
    def from_folder(self, folder, recursive=True):
        paths = LocalModelFinder().find(
            {
                "models_folder": folder,
                "recursive": recursive,
            }
        )
        return BatchInput([BatchInputItem(path) for path in paths])

    def from_paths(self, paths):
        return BatchInput([BatchInputItem(path) for path in paths])

    def from_rsn_routes(self, routes):
        paths = RsnModelListReader().parse(routes)
        return BatchInput([BatchInputItem(path) for path in paths])


class BatchInputPrompt(object):
    def __init__(self, input_factory=None):
        self.input_factory = input_factory or BatchInputFactory()

    def from_folder(
        self, recursive=True, title="Choose the folder containing Revit models"
    ):
        folder = forms.pick_folder(title=title)
        if not folder:
            return None
        return self.input_factory.from_folder(folder, recursive)


class BatchInputCsv(object):
    columns = ["SourcePath", "Options"]

    def load(self, file_path):
        items = []
        with codecs.open(file_path, "r", "utf-8-sig") as input_file:
            reader = csv.DictReader(input_file)
            if reader.fieldnames != self.columns:
                raise ValueError(
                    "Expected CSV columns: {}".format(", ".join(self.columns))
                )

            for row in reader:
                source_path = row["SourcePath"].strip()
                if not source_path:
                    continue
                options = json.loads(row["Options"] or "{}")
                items.append(BatchInputItem(source_path, options))

        return BatchInput(items)

    def save(self, batch_input, file_path):
        with codecs.open(file_path, "w", "utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=self.columns)
            writer.writeheader()
            for item in batch_input.items:
                writer.writerow(
                    {
                        "SourcePath": item.source_path,
                        "Options": json.dumps(item.options, ensure_ascii=False),
                    }
                )
