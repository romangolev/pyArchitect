# -*- coding: utf-8 -*-

import os

from pyrevit import forms

from tools.batch import widgets
from tools.batch.input import BatchInput, BatchInputCsv, BatchInputFactory
from tools.revit_documents import is_server_path

from System.Windows import Visibility
from System.Windows.Controls import Button
from System.Windows.Media import Color, SolidColorBrush


CHECKBOX_WIDTH = 25
PATH_WIDTH = 500
PROPERTY_WIDTH = 130


class BatchOptionsPresenter(object):
    selection_description = "Tick the models to include in this batch run."
    item_property_header = None
    bulk_label = None
    form = None

    def attach(self, form):
        """Give the presenter access to the hosting form before build()."""
        self.form = form

    def validation_error(self):
        """Return why Run must stay disabled, or None when the options are usable."""
        return None

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
    resolve_theme = True

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
        self._danger_brush = None

        self.options_presenter.attach(self)
        self.options_presenter.build(self.optionsHost)
        self._build_selection_header()
        self.btnBrowse.Click += self._browse
        self.btnLoadRoutes.Click += self._load_routes
        self.btnImportCsv.Click += self._import_csv
        self.btnContinue.Click += self._continue
        self.btnContinueOptions.Click += self._continue_to_options
        self.cbSelectAll.Click += self._select_all
        self.btnRun.Click += self._run
        self.btnCancel.Click += self._cancel

        if options_only:
            self.tabSelection.Visibility = Visibility.Collapsed
            self.tabProperties.Visibility = Visibility.Collapsed
            self.tabs.SelectedItem = self.tabOptions
            self.btnRun.Content = "Save options"

        self.refresh_run_state()

    def _model_error(self):
        """Why no batch can run yet, regardless of which tool is hosted.

        Every batch needs at least one ticked model, so this is checked by the
        form rather than left to each presenter's validation_error.
        """
        if not self.batch_input.items:
            return "Load models on the Selection tab first."
        for panel in self.lbModels.Items:
            if panel.Tag[1].IsChecked:
                return None
        return "Tick at least one model on the Selection properties tab."

    def refresh_run_state(self):
        """Enable Run only while the form and the presenter are both satisfied.

        Skipped when the form only edits options: saving settings is not a run,
        so an option left blank must still be storable.
        """
        if self.options_only:
            error = None
        else:
            error = self._model_error() or self.options_presenter.validation_error()
        self.btnRun.IsEnabled = not error
        self.btnRun.ToolTip = error
        self._accent_run_button(not error)

    def _hint_brush(self):
        """Brush for inline validation text, themed where the theme offers one."""
        if self._danger_brush is None:
            brush = self.TryFindResource("pyRevitDangerForegroundBrush")
            if brush is None:
                brush = SolidColorBrush(Color.FromRgb(0xFF, 0x6B, 0x61))
            self._danger_brush = brush
        return self._danger_brush

    def _hint(self, control, message=None):
        """Show a validation message beside a button, or clear it.

        Preferred over a modal alert: the message sits where the user already
        is, points at the tab that resolves it, and disappears on its own once
        the form moves on.
        """
        if not message:
            control.Visibility = Visibility.Collapsed
            return
        control.Text = message
        control.Foreground = self._hint_brush()
        control.Visibility = Visibility.Visible

    def _accent_run_button(self, highlighted):
        """Paint Run in the theme accent while it can actually be pressed.

        Assigned from here rather than from a style in the XAML: a
        <Window.Resources> block would replace the resource dictionary pyRevit
        merges into the window before the XAML is parsed, taking the theme with
        it.  Both brushes exist in every pyRevit version that themes forms.
        """
        for prop, key in (
            ("Background", "pyRevitAccentBrush"),
            ("BorderBrush", "pyRevitAccentBrush"),
            ("Foreground", "pyRevitDarkBrush"),
        ):
            brush = self.TryFindResource(key) if highlighted else None
            if brush is None:
                self.btnRun.ClearValue(getattr(Button, prop + "Property"))
            else:
                setattr(self.btnRun, prop, brush)

    def default_export_folder(self):
        """Folder to seed an export path from, or '' when none applies.

        Prefers the folder the models were loaded from, then the folder the
        loaded local models share.  RSN routes have no local folder.
        """
        folder = self.tbFolder.Text.strip()
        if folder and os.path.isdir(folder):
            return folder
        folders = set(
            os.path.dirname(item.source_path)
            for item in self.batch_input.items
            if not is_server_path(item.source_path)
        )
        folders.discard("")
        return folders.pop() if len(folders) == 1 else ""

    def loaded_items(self):
        """Items currently loaded on the selection tab."""
        return self.batch_input.items

    def selected_items(self):
        """Items ticked for the pending run, without committing the form."""
        return [
            panel.Tag[0]
            for panel in self.lbModels.Items
            if panel.Tag[1].IsChecked
        ]

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
            self._hint(
                self.tbSelectionHint,
                u"No models loaded \u2014 pick a folder or add RSN routes above.",
            )
            return
        self._hint(self.tbSelectionHint)
        self.tabs.SelectedItem = self.tabProperties

    def _continue_to_options(self, sender, args):
        self.tabs.SelectedItem = self.tabOptions

    def _render_items(self):
        self.lbModels.Items.Clear()
        self.tabProperties.IsEnabled = bool(self.batch_input.items)
        for item in self.batch_input.items:
            checkbox = widgets.checkbox(checked=True, width=25)
            checkbox.Click += self._model_ticked
            controls = [checkbox, widgets.text(item.source_path, width=500)]
            property_control = self.options_presenter.create_item_property(item)
            if property_control:
                property_control.Width = PROPERTY_WIDTH
                controls.append(property_control)
            panel = widgets.row(*controls)
            panel.Tag = (item, checkbox, property_control)
            self.lbModels.Items.Add(panel)
        self._hint(self.tbSelectionHint)
        self.refresh_run_state()

    def _model_ticked(self, sender, args):
        self.refresh_run_state()

    def _select_all(self, sender, args):
        selected = bool(self.cbSelectAll.IsChecked)
        for panel in self.lbModels.Items:
            panel.Tag[1].IsChecked = selected
        self.refresh_run_state()

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
            self.refresh_run_state()
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
