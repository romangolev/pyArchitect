# -*- coding: utf-8 -*-

import os

from pyrevit import forms

from tools.batch import widgets
from tools.batch.input import BatchInput, BatchInputCsv, BatchInputFactory

from System.Windows import Visibility


CHECKBOX_WIDTH = 25
PATH_WIDTH = 500
PROPERTY_WIDTH = 130


class BatchOptionsPresenter(object):
    selection_description = "Tick the models to include in this batch run."
    item_property_header = None
    bulk_label = None

    def build(self, host):
        raise NotImplementedError

    def create_item_property(self, item):
        return None

    def read_item_property(self, item, control):
        return item.options

    def create_bulk_control(self):
        """Return a control whose value can be pushed onto every row."""
        return None

    def apply_bulk_value(self, bulk_control, property_control):
        """Copy the bulk control's value onto one row's property control."""

    def read_options(self):
        raise NotImplementedError


class BatchSelectionForm(forms.WPFWindow):
    def __init__(self, title, options_presenter, options_only=False):
        xaml_path = os.path.join(os.path.dirname(__file__), "batch_form.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        self.Title = title
        self.options_presenter = options_presenter
        self.options_only = options_only
        self.input_factory = BatchInputFactory()
        self.input_csv = BatchInputCsv()
        self.batch_input = BatchInput()
        self.bulk_control = None
        self.result = None

        self.options_presenter.build(self.optionsHost)
        self._build_selection_header()
        self.btnBrowse.Click += self._browse
        self.btnLoadRoutes.Click += self._load_routes
        self.btnImportCsv.Click += self._import_csv
        self.btnContinue.Click += self._continue
        self.cbSelectAll.Click += self._select_all
        self.btnRun.Click += self._run
        self.btnCancel.Click += self._cancel

        if options_only:
            self.tabSelection.Visibility = Visibility.Collapsed
            self.tabProperties.Visibility = Visibility.Collapsed
            self.tabs.SelectedItem = self.tabOptions
            self.btnRun.Content = "Save options"

    def _build_selection_header(self):
        presenter = self.options_presenter
        self.tbSelectionDescription.Text = presenter.selection_description

        self.columnHeader.Children.Add(widgets.text("", width=CHECKBOX_WIDTH))
        self.columnHeader.Children.Add(
            widgets.text("Model", width=PATH_WIDTH, bold=True)
        )
        if presenter.item_property_header:
            self.columnHeader.Children.Add(
                widgets.text(
                    presenter.item_property_header, width=PROPERTY_WIDTH, bold=True
                )
            )

        self.bulk_control = presenter.create_bulk_control()
        if self.bulk_control is None:
            self.bulkHost.Visibility = Visibility.Collapsed
            return

        self.bulk_control.Width = PROPERTY_WIDTH
        apply_button = widgets.button("Apply to all", width=110, margin=(8, 0, 0, 0))
        apply_button.Click += self._apply_bulk_value
        self.bulkHost.Children.Add(
            widgets.text(
                presenter.bulk_label or "Set for all models",
                width=CHECKBOX_WIDTH + PATH_WIDTH,
                centered=True,
            )
        )
        self.bulkHost.Children.Add(self.bulk_control)
        self.bulkHost.Children.Add(apply_button)

    def _apply_bulk_value(self, sender, args):
        for panel in self.lbModels.Items:
            property_control = panel.Tag[2]
            if property_control is not None:
                self.options_presenter.apply_bulk_value(
                    self.bulk_control, property_control
                )

    def _browse(self, sender, args):
        folder = forms.pick_folder()
        if not folder:
            return
        self.tbFolder.Text = folder
        self._load_folder()

    def _load_folder(self):
        folder = self.tbFolder.Text.strip()
        if not folder:
            return
        self.batch_input = self.input_factory.from_folder(
            folder,
            bool(self.cbRecursive.IsChecked),
        )
        self._render_items()

    def _load_routes(self, sender, args):
        self.batch_input = self.input_factory.from_rsn_routes(self.tbRoutes.Text)
        self._render_items()

    def _import_csv(self, sender, args):
        file_path = forms.pick_file(file_ext="csv")
        if not file_path:
            return
        try:
            self.batch_input = self.input_csv.load(file_path)
        except Exception as exception:
            forms.alert("Cannot read batch CSV: {}".format(exception), title=self.Title)
            return
        self._render_items()

    def _continue(self, sender, args):
        if self.sourceTabs.SelectedIndex == 0:
            self._load_folder()
        if not self.batch_input.items:
            forms.alert("No models loaded.", title=self.Title)
            return
        self.tabs.SelectedItem = self.tabProperties

    def _render_items(self):
        self.lbModels.Items.Clear()
        self.tabProperties.IsEnabled = bool(self.batch_input.items)
        for item in self.batch_input.items:
            checkbox = widgets.checkbox(checked=True, width=25)
            controls = [checkbox, widgets.text(item.source_path, width=500)]
            property_control = self.options_presenter.create_item_property(item)
            if property_control:
                property_control.Width = PROPERTY_WIDTH
                controls.append(property_control)
            panel = widgets.row(*controls)
            panel.Tag = (item, checkbox, property_control)
            self.lbModels.Items.Add(panel)

    def _select_all(self, sender, args):
        selected = bool(self.cbSelectAll.IsChecked)
        for panel in self.lbModels.Items:
            panel.Tag[1].IsChecked = selected

    def _run(self, sender, args):
        if self.options_only:
            self.result = {"options": self.options_presenter.read_options()}
            self.Close()
            return

        selected_items = []
        for panel in self.lbModels.Items:
            item, checkbox, property_control = panel.Tag
            if not checkbox.IsChecked:
                continue
            item.options = self.options_presenter.read_item_property(
                item, property_control
            )
            selected_items.append(item)
        if not selected_items:
            forms.alert("Select at least one model.", title=self.Title)
            return
        self.result = {
            "input": BatchInput(selected_items),
            "options": self.options_presenter.read_options(),
        }
        self.Close()

    def _cancel(self, sender, args):
        self.result = None
        self.Close()


def show_batch_form(title, options_presenter, options_only=False):
    form = BatchSelectionForm(title, options_presenter, options_only)
    form.ShowDialog()
    return form.result
