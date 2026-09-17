# -*- coding: utf-8 -*-

import os

from pyrevit import forms

from tools.batch import widgets
from tools.batch.form import BatchOptionsPresenter, show_batch_form
from tools.revit_documents import is_server_path
from tools.navis.profiles import load_profiles


class NavisOptionsPresenter(BatchOptionsPresenter):
    selection_description = (
        "Tick the models that should get a Navisworks view. The profile decides which "
        "categories are hidden in that view; it is guessed from the file name and can "
        "be changed per model below."
    )
    item_property_header = "Profile"
    bulk_label = "Set the same profile for every model:"

    def __init__(self, profiles=None):
        self.profiles = profiles or load_profiles()
        self.hidden_worksets = None
        self.analysis_only = None
        self.upgrade_models = None
        self.create_log = None
        self.log_folder = None
        self.copy_destination = None

    def build(self, host):
        self.hidden_worksets = widgets.textbox()
        self.analysis_only = widgets.checkbox("Analysis only")
        self.upgrade_models = widgets.checkbox("Allow model upgrade")
        self.create_log = widgets.checkbox("Save an additional report copy", True)
        self.log_folder = widgets.textbox()
        self.copy_destination = widgets.textbox()
        self.copy_destination.TextChanged += self._copy_destination_changed
        browse_copies = widgets.button("Browse...", width=90, margin=(8, 0, 0, 0))
        browse_copies.Click += self._pick_copy_destination
        host.Children.Add(
            widgets.stack(
                widgets.group(
                    "Output copies (required)",
                    widgets.text(
                        "Each selected RVT is copied to this folder before the "
                        "Navisworks view is created. Source models are not edited."
                    ),
                    widgets.fill_row(self.copy_destination, browse_copies),
                ),
                widgets.label("Hidden worksets (comma-separated name fragments)"),
                self.hidden_worksets,
                self.analysis_only,
                self.upgrade_models,
                self.create_log,
                widgets.label("Report folder"),
                self.log_folder,
            )
        )

    def _pick_copy_destination(self, sender, args):
        folder = forms.pick_folder()
        if folder:
            self.copy_destination.Text = folder

    def _copy_destination_changed(self, sender, args):
        if self.form:
            self.form.refresh_run_state()

    def validation_error(self):
        if self.copy_destination is None or not self.copy_destination.Text.strip():
            return "Choose an output folder for the Navisworks model copies on the Options tab."

        destination = self.copy_destination.Text.strip()
        if not os.path.isdir(destination):
            return "The selected copy destination does not exist."

        items = self.form.selected_items() if self.form else []
        names = set()
        for item in items:
            if is_server_path(item.source_path):
                return "Revit Server routes cannot be copied to a local output folder."
            target = os.path.join(destination, os.path.basename(item.source_path))
            if os.path.normcase(os.path.abspath(target)) == os.path.normcase(
                os.path.abspath(item.source_path)
            ):
                return "Choose an output folder different from the source model folder."
            target_key = os.path.normcase(target)
            if target_key in names:
                return "Selected models have the same file name; choose fewer models or rename one."
            names.add(target_key)
            if os.path.exists(target):
                return "A destination copy already exists: {}".format(target)
        return None

    def create_item_property(self, item):
        selected = item.options.get("profile", self.profiles.guess(item.name))
        return widgets.combobox(
            self.profiles.captions,
            self.profiles.index_of(selected),
        )

    def create_bulk_control(self):
        return widgets.combobox(
            self.profiles.captions,
            self.profiles.index_of(self.profiles.default_id),
        )

    def apply_bulk_value(self, bulk_control, property_control):
        property_control.SelectedIndex = bulk_control.SelectedIndex

    def read_item_property(self, item, control):
        options = dict(item.options)
        profile = self.profiles.at(control.SelectedIndex)
        options["profile"] = profile.id if profile else self.profiles.default_id
        return options

    def read_options(self):
        return {
            "analysis_only": bool(self.analysis_only.IsChecked),
            "upgrade_models": bool(self.upgrade_models.IsChecked),
            "hidden_worksets": [
                value.strip()
                for value in self.hidden_worksets.Text.split(",")
                if value.strip()
            ],
            "create_log": bool(self.create_log.IsChecked),
            "log_folder": self.log_folder.Text.strip(),
            "copy_destination": self.copy_destination.Text.strip(),
        }


def show_form():
    result = show_batch_form("Batch Navisworks view", NavisOptionsPresenter())
    if not result:
        return None, None
    return result["input"].items, result["options"]
