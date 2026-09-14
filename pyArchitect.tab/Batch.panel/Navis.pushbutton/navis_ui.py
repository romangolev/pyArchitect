# -*- coding: utf-8 -*-

from tools.batch import widgets
from tools.batch.form import BatchOptionsPresenter, show_batch_form
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

    def build(self, host):
        self.hidden_worksets = widgets.textbox()
        self.analysis_only = widgets.checkbox("Analysis only")
        self.upgrade_models = widgets.checkbox("Allow model upgrade")
        self.create_log = widgets.checkbox("Save an additional report copy", True)
        self.log_folder = widgets.textbox()
        host.Children.Add(
            widgets.stack(
                widgets.label("Hidden worksets (comma-separated name fragments)"),
                self.hidden_worksets,
                self.analysis_only,
                self.upgrade_models,
                self.create_log,
                widgets.label("Report folder"),
                self.log_folder,
            )
        )

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
        }


def show_form():
    result = show_batch_form("Batch Navisworks view", NavisOptionsPresenter())
    if not result:
        return None, None
    return result["input"].items, result["options"]
