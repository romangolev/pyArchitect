# -*- coding: utf-8 -*-

from System.Windows import Thickness
from System.Windows.Controls import CheckBox, ComboBox, StackPanel, TextBlock, TextBox

from tools.batch.form import BatchOptionsPresenter, show_batch_form
from tools.navis.profiles import PROFILE_ITEMS


class NavisOptionsPresenter(BatchOptionsPresenter):
    def __init__(self):
        self.hidden_worksets = None
        self.analysis_only = None
        self.upgrade_models = None
        self.create_log = None
        self.log_folder = None

    def build(self, host):
        panel = StackPanel()
        panel.Children.Add(
            self._label("Hidden worksets (comma-separated name fragments)")
        )
        self.hidden_worksets = TextBox()
        panel.Children.Add(self.hidden_worksets)
        self.analysis_only = CheckBox()
        self.analysis_only.Content = "Analysis only"
        panel.Children.Add(self.analysis_only)
        self.upgrade_models = CheckBox()
        self.upgrade_models.Content = "Allow model upgrade"
        panel.Children.Add(self.upgrade_models)
        self.create_log = CheckBox()
        self.create_log.Content = "Save an additional report copy"
        self.create_log.IsChecked = True
        panel.Children.Add(self.create_log)
        panel.Children.Add(self._label("Report folder"))
        self.log_folder = TextBox()
        panel.Children.Add(self.log_folder)
        host.Children.Add(panel)

    def create_item_property(self, item):
        profile = ComboBox()
        profile.Width = 130
        for caption, value in PROFILE_ITEMS:
            profile.Items.Add(caption)
            if value == item.options.get("profile", self._guess_profile(item.name)):
                profile.SelectedItem = caption
        return profile

    def read_item_property(self, item, control):
        options = dict(item.options)
        caption = str(control.SelectedItem)
        for name, value in PROFILE_ITEMS:
            if name == caption:
                options["profile"] = value
                break
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

    @staticmethod
    def _label(text):
        label = TextBlock()
        label.Text = text
        label.Margin = Thickness(0, 8, 0, 2)
        return label

    @staticmethod
    def _guess_profile(file_name):
        name = file_name.upper()
        for marker, profile in [
            ("АР", "AR"),
            ("КР", "KR"),
            ("ОВ", "OV"),
            ("ВК", "VK"),
            ("ЭОМ", "EOM"),
        ]:
            if marker in name:
                return profile
        return "UNIVERSAL"


def show_form():
    result = show_batch_form("Batch Navisworks view", NavisOptionsPresenter())
    if not result:
        return None
    settings = result["options"]
    settings["selected_models"] = [
        {"path": item.source_path, "profile": item.options.get("profile", "UNIVERSAL")}
        for item in result["input"].items
    ]
    return settings


def show_options_form():
    return show_batch_form("Navisworks view options", NavisOptionsPresenter(), True)
