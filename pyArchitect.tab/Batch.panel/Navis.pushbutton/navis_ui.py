# -*- coding: utf-8 -*-

from pyrevit import forms

from System.Windows.Controls import CheckBox, ComboBox, TextBlock, StackPanel

from System.Windows import (
    Thickness,
)


from tools.model_sources import ModelSourceResolver
from tools.batch.input import BatchInputCsv

from tools.navis.profiles import PROFILE_ITEMS

from tools.rsn import RsnModelListReader


class NavisForm(forms.WPFWindow):
    def btnApplyProfile_Click(self, sender, args):

        caption = str(self.cmbBulkProfile.SelectedItem)

        for item in self.lbModels.Items:
            try:
                data = item.Tag

                cb = data["checkbox"]

                if not cb.IsChecked:
                    continue

                data["profile"].SelectedItem = caption

            except:
                pass

    def load_bulk_profiles(self):

        self.cmbBulkProfile.Items.Clear()

        for caption, value in PROFILE_ITEMS:
            self.cmbBulkProfile.Items.Add(caption)

        self.cmbBulkProfile.SelectedIndex = 0

    def __init__(self):

        forms.WPFWindow.__init__(self, "NavisForm.xaml")

        self.settings = None
        self.model_source_resolver = ModelSourceResolver()
        self.batch_input_csv = BatchInputCsv()
        self.rsn_model_list_reader = RsnModelListReader()

        self.btnApplyProfile.Click += self.btnApplyProfile_Click

        self.load_bulk_profiles()

        self.update_controls(None, None)

        self.btnBrowse.Click += self.btnBrowse_Click

        self.btnLoadServerModels.Click += self.btnLoadServerModels_Click

        self.btnImportCsv.Click += self.btnImportCsv_Click

        self.btnClearServerModels.Click += self.btnClearServerModels_Click

        self.btnBrowseLog.Click += self.btnBrowseLog_Click

        self.btnOK.Click += self.btnOK_Click

        self.btnCancel.Click += self.btnCancel_Click

        self.cbCreateLog.Click += self.update_controls

        self.cbSelectAll.Click += self.cbSelectAll_Click

        self.cbRecursive.Click += self.search_settings_changed

        self.update_controls(None, None)

    def update_controls(self, sender, args):

        create_log = bool(self.cbCreateLog.IsChecked)

        self.tbLogFolder.IsEnabled = create_log

        self.btnBrowseLog.IsEnabled = create_log

    def load_models(self):

        self.lbModels.Items.Clear()

        source = "LOCAL" if self.tabSource.SelectedIndex == 0 else "RSN"

        settings = {
            "source": source,
            "models_folder": self.tbFolder.Text,
            "recursive": bool(self.cbRecursive.IsChecked),
            "server_models": self.tbServerModels.Text,
        }

        files = self.model_source_resolver.resolve(settings)

        files.sort()

        self.gbModels.Header = "ÐÐ°Ð¹Ð´ÐµÐ½Ð½Ñ‹Ðµ Ð¼Ð¾Ð´ÐµÐ»Ð¸ ({})".format(len(files))

        for file_path in files:
            self.lbModels.Items.Add(self.create_model_item(file_path))

    def btnBrowse_Click(self, sender, args):

        folder = forms.pick_folder()

        if not folder:
            return

        self.tbFolder.Text = folder

        self.tbLogFolder.Text = folder

        self.load_models()

    def btnClearServerModels_Click(self, sender, args):

        self.tbServerModels.Text = ""

        self.lbModels.Items.Clear()

        self.gbModels.Header = "ÐÐ°Ð¹Ð´ÐµÐ½Ð½Ñ‹Ðµ Ð¼Ð¾Ð´ÐµÐ»Ð¸ (0)"

    def btnImportCsv_Click(self, sender, args):

        csv = forms.pick_file(file_ext="csv")

        if not csv:
            return

        try:
            batch_input = self.batch_input_csv.load(csv)
        except:
            models = self.rsn_model_list_reader.read_csv(csv)
            self.tbServerModels.Text = "\n".join(models)
            self.load_models()
            return

        self.load_batch_input(batch_input)

    def search_settings_changed(self, sender, args):

        if self.tabSource.SelectedIndex != 0:
            return

        print("SEARCH SETTINGS CHANGED")

        self.load_models()

    def cbSelectAll_Click(self, sender, args):

        state = bool(self.cbSelectAll.IsChecked)

        for item in self.lbModels.Items:
            try:
                item.Tag["checkbox"].IsChecked = state

            except:
                pass

    def btnBrowseLog_Click(self, sender, args):

        folder = forms.pick_folder()

        if folder:
            self.tbLogFolder.Text = folder

    def guess_profile(self, file_name):

        name = file_name.upper()

        if "ÐÐ " in name:
            return "AR"

        if "ÐšÐ " in name:
            return "KR"

        if "ÐžÐ’" in name:
            return "OV"

        if "Ð’Ðš" in name:
            return "VK"

        if "Ð­ÐžÐœ" in name:
            return "EOM"

        return "UNIVERSAL"

    def load_batch_input(self, batch_input):
        self.lbModels.Items.Clear()

        for item in batch_input.items:
            self.lbModels.Items.Add(
                self.create_model_item(item.source_path, item.options.get("profile"))
            )

        self.gbModels.Header = "Found models ({})".format(len(batch_input.items))

    def create_model_item(self, file_path, profile=None):

        file_name = file_path.replace("\\", "/").split("/")[-1]

        panel = StackPanel()

        panel.Orientation = 0

        panel.Margin = Thickness(0, 2, 0, 2)

        cb = CheckBox()

        cb.IsChecked = True

        cb.Width = 25

        panel.Children.Add(cb)

        tb = TextBlock()

        tb.Text = file_name

        tb.Width = 550

        tb.Margin = Thickness(5, 3, 10, 0)

        panel.Children.Add(tb)

        cmb = ComboBox()

        cmb.Width = 140

        for caption, value in PROFILE_ITEMS:
            cmb.Items.Add(caption)

        current_profile = profile or self.guess_profile(file_name)

        for caption, value in PROFILE_ITEMS:
            if value == current_profile:
                cmb.SelectedItem = caption

                break

        panel.Children.Add(cmb)

        panel.Tag = {"checkbox": cb, "path": file_path, "profile": cmb}

        return panel

    def btnOK_Click(self, sender, args):

        selected_models = []

        for item in self.lbModels.Items:
            data = item.Tag

            if not data["checkbox"].IsChecked:
                continue

            caption = str(data["profile"].SelectedItem)

            profile = "UNIVERSAL"

            for c, v in PROFILE_ITEMS:
                if c == caption:
                    profile = v
                    break

            selected_models.append({"path": data["path"], "profile": profile})

        hidden_worksets = [
            item.strip()
            for item in self.tbHiddenWorksets.Text.split(",")
            if item.strip()
        ]

        source = "LOCAL" if self.tabSource.SelectedIndex == 0 else "RSN"

        self.settings = {
            "source": source,
            "models_folder": self.tbFolder.Text,
            "recursive": bool(self.cbRecursive.IsChecked),
            "server_models": self.tbServerModels.Text,
            "selected_models": selected_models,
            "analysis_only": bool(self.cbAnalysisOnly.IsChecked),
            "upgrade_models": bool(self.cbUpgradeModels.IsChecked),
            "hidden_worksets": hidden_worksets,
            "create_log": bool(self.cbCreateLog.IsChecked),
            "log_folder": self.tbLogFolder.Text,
        }

        self.Close()

    def btnCancel_Click(self, sender, args):

        self.settings = None

        self.Close()

    def btnLoadServerModels_Click(self, sender, args):

        if not self.tbServerModels.Text.strip():
            forms.alert("Ð¡Ð¿Ð¸ÑÐ¾Ðº Ð¼Ð¾Ð´ÐµÐ»ÐµÐ¹ Ð¿ÑƒÑÑ‚.")

            return

        self.load_models()


def show_form():

    form = NavisForm()

    form.ShowDialog()

    return form.settings
