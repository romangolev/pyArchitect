# -*- coding: utf-8 -*-

import os

from pyrevit import forms

from tools.batch import widgets
from tools.batch.form import BatchOptionsPresenter, show_batch_form
from tools.batch.strings import S
from tools.revit_documents import is_server_path
from tools.navis.profiles import load_profiles


DEFAULT_COPY_FOLDER = "Navisworks"
WRITE_MODE_GROUP = "navis_write_mode"


class NavisOptionsPresenter(BatchOptionsPresenter):
    COPY_OUTPUT = "copy_output"
    EDIT_SOURCES = "edit_sources"

    source_description = S("form.source_description")
    selection_description = S("navis.selection_description")
    options_description = S("navis.options_description")
    item_property_header = S("navis.column.profile")
    bulk_label = S("navis.bulk_label")

    def __init__(self, profiles=None):
        self.profiles = profiles or load_profiles()
        self.hidden_worksets = None
        self.analysis_only = None
        self.upgrade_models = None
        self.copy_destination = None
        self.write_copies = None
        self.write_in_place = None
        self.copy_output_group = None

    def build(self, host):
        self.hidden_worksets = widgets.textbox()
        self.analysis_only = widgets.checkbox(S("navis.option.analysis_only"))
        self.upgrade_models = widgets.checkbox(S("navis.option.upgrade_models"))
        self.copy_destination = widgets.FolderPicker(
            pick_tooltip=S("navis.tooltip.output_folder"),
            on_default=self._default_copy_destination,
            default_tooltip=S(
                "navis.tooltip.default_output_folder", DEFAULT_COPY_FOLDER
            ),
            on_change=self._copy_destination_changed,
        )
        self.write_copies = widgets.radiobutton(
            S("navis.option.write_copies"),
            group=WRITE_MODE_GROUP,
            margin=(0, 0, 0, 5),
        )
        self.write_in_place = widgets.radiobutton(
            S("navis.option.write_in_place"),
            group=WRITE_MODE_GROUP,
        )
        self.write_copies.Checked += self._write_mode_changed
        self.write_in_place.Checked += self._write_mode_changed
        self.copy_output_group = widgets.group(
            S("navis.group.output_copies"),
            widgets.text(S("navis.output_copies_hint")),
            self.copy_destination.control,
            margin=(0, 14, 0, 0),
        )
        self.copy_output_group.IsEnabled = False
        host.Children.Add(
            widgets.stack(
                widgets.group(
                    S("navis.group.save_mode"),
                    self.write_copies,
                    self.write_in_place,
                ),
                self.copy_output_group,
                widgets.separator((0, 16, 0, 0)),
                widgets.label(S("navis.label.hidden_worksets")),
                self.hidden_worksets,
                self.analysis_only,
                self.upgrade_models,
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
                S("navis.alert.no_default_output"),
                title=S("navis.title"),
            )
            return ""
        folder = os.path.join(source, DEFAULT_COPY_FOLDER)
        if not os.path.isdir(folder):
            try:
                os.makedirs(folder)
            except Exception as exception:
                forms.alert(
                    S("navis.alert.cannot_create_output", folder, exception),
                    title=S("navis.title"),
                )
                return ""
        return folder

    def _copy_destination_changed(self, sender, args):
        if self.form:
            self.form.refresh_run_state()

    def _write_mode_changed(self, sender, args):
        if self.copy_output_group:
            self.copy_output_group.IsEnabled = bool(self.write_copies.IsChecked)
        if self.form:
            self.form.refresh_run_state()

    def validation_error(self):
        if self.write_copies is None:
            return None
        if not (self.write_copies.IsChecked or self.write_in_place.IsChecked):
            return S("navis.error.no_save_mode")
        if self.write_in_place.IsChecked:
            return None
        if self.copy_destination is None or not self.copy_destination.path:
            return S("navis.error.no_output_folder")

        destination = self.copy_destination.path
        if not os.path.isdir(destination):
            return S("navis.error.output_missing")

        items = self.form.selected_items() if self.form else []
        names = set()
        for item in items:
            if is_server_path(item.source_path):
                return S("navis.error.rsn_copy")
            target = os.path.join(destination, os.path.basename(item.source_path))
            if os.path.normcase(os.path.abspath(target)) == os.path.normcase(
                os.path.abspath(item.source_path)
            ):
                return S("navis.error.same_folder")
            target_key = os.path.normcase(target)
            if target_key in names:
                return S("navis.error.duplicate_names")
            names.add(target_key)
            if os.path.exists(target):
                return S("navis.error.copy_exists", target)
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
            "save_mode": (
                self.COPY_OUTPUT
                if self.write_copies.IsChecked
                else self.EDIT_SOURCES
            ),
            "copy_destination": (
                self.copy_destination.path if self.write_copies.IsChecked else ""
            ),
        }


def show_form():
    result = show_batch_form(S("navis.title"), NavisOptionsPresenter())
    if not result:
        return None, None
    return result["input"].items, result["options"]
