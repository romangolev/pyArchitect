# -*- coding: utf-8 -*-

import os

from pyrevit import forms

from tools.batch import widgets
from tools.batch.form import BatchOptionsPresenter, show_batch_form
from tools.revit_documents import is_server_path
from tools.navis.profiles import load_profiles


DEFAULT_COPY_FOLDER = "Navisworks"


class NavisOptionsPresenter(BatchOptionsPresenter):
    COPY_OUTPUT = "copy_output"
    EDIT_SOURCES = "edit_sources"

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
        self.write_mode = None
        self.copy_output_group = None

    def build(self, host):
        self.hidden_worksets = widgets.textbox()
        self.analysis_only = widgets.checkbox("Analysis only")
        self.upgrade_models = widgets.checkbox("Allow model upgrade")
        self.create_log = widgets.checkbox("Save an additional report copy", True)
        self.log_folder = widgets.FolderPicker(
            pick_tooltip="Pick the report folder"
        )
        self.copy_destination = widgets.FolderPicker(
            pick_tooltip="Pick the output folder",
            on_default=self._default_copy_destination,
            default_tooltip="Use a '{}' folder beside the models".format(
                DEFAULT_COPY_FOLDER
            ),
            on_change=self._copy_destination_changed,
        )
        self.write_mode = widgets.combobox(
            [
                "Create and modify output copies (source models stay untouched)",
                "Edit and save selected source models in place",
            ],
            -1,
        )
        self.write_mode.SelectionChanged += self._write_mode_changed
        self.copy_output_group = widgets.group(
            "Output copies",
            widgets.text(
                "Each selected RVT is copied to this folder before the "
                "Navisworks view is created. Source models are not edited."
            ),
            self.copy_destination.control,
        )
        self.copy_output_group.IsEnabled = False
        host.Children.Add(
            widgets.stack(
                widgets.group(
                    "Where should the Navisworks view be saved? (required)",
                    self.write_mode,
                ),
                self.copy_output_group,
                widgets.label("Hidden worksets (comma-separated name fragments)"),
                self.hidden_worksets,
                self.analysis_only,
                self.upgrade_models,
                self.create_log,
                widgets.label("Report folder"),
                self.log_folder.control,
            )
        )

    def _default_copy_destination(self):
        """Point the copies at a subfolder beside the loaded models.

        A subfolder rather than the models' own folder: copying a model over
        itself is rejected by validation_error, so the models' folder can never
        be the default.  The folder is created because an output folder that
        does not exist yet fails validation too, leaving a dead end.
        """
        source = self.form.default_export_folder() if self.form else ""
        if not source:
            forms.alert(
                "No default output folder is available. Revit Server routes have "
                "no local folder, so pick an output folder instead.",
                title="Batch NavisView",
            )
            return ""
        folder = os.path.join(source, DEFAULT_COPY_FOLDER)
        if not os.path.isdir(folder):
            try:
                os.makedirs(folder)
            except Exception as exception:
                forms.alert(
                    "Cannot create the default output folder:\n{}\n{}".format(
                        folder, exception
                    ),
                    title="Batch NavisView",
                )
                return ""
        return folder

    def _copy_destination_changed(self, sender, args):
        if self.form:
            self.form.refresh_run_state()

    def _write_mode_changed(self, sender, args):
        if self.copy_output_group:
            self.copy_output_group.IsEnabled = (
                self.write_mode.SelectedIndex == 0
            )
        if self.form:
            self.form.refresh_run_state()

    def validation_error(self):
        if self.write_mode is None or self.write_mode.SelectedIndex < 0:
            return "Choose whether to create output copies or edit the source models on the Options tab."
        if self.write_mode.SelectedIndex == 1:
            return None
        if self.copy_destination is None or not self.copy_destination.path:
            return "Choose an output folder for the Navisworks model copies on the Options tab."

        destination = self.copy_destination.path
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
            "log_folder": self.log_folder.path,
            "save_mode": (
                self.COPY_OUTPUT
                if self.write_mode.SelectedIndex == 0
                else self.EDIT_SOURCES
            ),
            "copy_destination": (
                self.copy_destination.path
                if self.write_mode.SelectedIndex == 0
                else ""
            ),
        }


def show_form():
    result = show_batch_form("Batch NavisView", NavisOptionsPresenter())
    if not result:
        return None, None
    return result["input"].items, result["options"]
