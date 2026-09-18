# -*- coding: utf-8 -*-
"""Small WPF control factories shared by the batch option presenters."""

import clr

clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
clr.AddReference("WindowsBase")

from System.Windows import FontWeights, Thickness, VerticalAlignment
from System.Windows import TextTrimming
from System.Windows.Media import FontFamily
from System.Windows.Controls import (
    Button,
    CheckBox,
    ColumnDefinition,
    ComboBox,
    Dock,
    DockPanel,
    Grid,
    Orientation,
    RadioButton,
    Separator,
    StackPanel,
    TextBlock,
    TextBox,
)


COLUMN_GUTTER = 28

FOLDER_GLYPH = u"\uED25"
DEFAULT_FOLDER_GLYPH = u"\uE80F"


def text(value, width=None, bold=False, centered=False, trim=False):
    control = TextBlock()
    control.Text = value
    if width:
        control.Width = width
    if trim:
        control.TextTrimming = TextTrimming.CharacterEllipsis
    if bold:
        control.FontWeight = FontWeights.Bold
    if centered:
        control.VerticalAlignment = VerticalAlignment.Center
    return control


def label(value):
    control = text(value)
    control.Margin = Thickness(0, 8, 0, 2)
    return control


def checkbox(content="", checked=False, width=None, margin=None):
    control = CheckBox()
    control.Content = content
    control.IsChecked = checked
    if width:
        control.Width = width
    if margin:
        control.Margin = Thickness(*margin)
    return control


def radiobutton(content="", checked=False, group=None, margin=None):
    """One choice in a set. Leave every option unchecked to force a decision."""
    control = RadioButton()
    control.Content = content
    control.IsChecked = checked
    if group:
        control.GroupName = group
    if margin:
        control.Margin = Thickness(*margin)
    return control


def textbox(text="", width=None):
    """Single-line text box.

    Centred vertically and given a little side padding: pyRevit's theme sets
    no padding and leaves content top-aligned, so in a row sized by the 26px
    icon buttons the text otherwise sits high and hard against the border.
    """
    control = TextBox()
    control.Text = text
    control.VerticalContentAlignment = VerticalAlignment.Center
    control.Padding = Thickness(4, 0, 4, 0)
    if width:
        control.Width = width
    return control


def combobox(items, selected_index=None, width=None):
    control = ComboBox()
    for item in items:
        control.Items.Add(item)
    if selected_index is not None:
        control.SelectedIndex = selected_index
    if width:
        control.Width = width
    return control


def button(content, width=None, margin=None):
    control = Button()
    control.Content = content
    if width:
        control.Width = width
    if margin:
        control.Margin = Thickness(*margin)
    return control


def icon_button(glyph, tooltip=None, margin=(4, 0, 0, 0)):
    """Square glyph button matching pyRevit's own small toolbar buttons."""
    control = button(glyph, width=26, margin=margin)
    control.Height = 26
    control.Padding = Thickness(0)
    control.FontFamily = FontFamily("Segoe MDL2 Assets")
    control.FontSize = 13
    if tooltip:
        control.ToolTip = tooltip
    return control


def _panel(orientation, controls):
    panel = StackPanel()
    panel.Orientation = orientation
    for control in controls:
        panel.Children.Add(control)
    return panel


def stack(*controls):
    return _panel(Orientation.Vertical, controls)


def row(*controls):
    return _panel(Orientation.Horizontal, controls)


def separator(margin=None):
    """Hairline rule; pyRevit's theme paints it with the control border brush."""
    control = Separator()
    if margin:
        control.Margin = Thickness(*margin)
    return control


def group(title, *controls, **kwargs):
    """Titled block: a bold caption over a hairline rule, then the controls.

    Pass `margin` to space it from whatever sits above; stacked groups need it,
    since the caption would otherwise butt straight against the block before.
    """
    caption = text(title, bold=True)
    caption.Margin = Thickness(0, 0, 0, 3)
    panel = stack(caption, separator((0, 0, 0, 8)), *controls)
    margin = kwargs.get("margin")
    if margin:
        panel.Margin = Thickness(*margin)
    return panel


def columns(*panels, **kwargs):
    """Equal-width columns with a gutter between them."""
    gutter = kwargs.get("gutter", COLUMN_GUTTER)
    grid = Grid()
    for index, panel in enumerate(panels):
        grid.ColumnDefinitions.Add(ColumnDefinition())
        if index:
            panel.Margin = Thickness(gutter, 0, 0, 0)
        Grid.SetColumn(panel, index)
        grid.Children.Add(panel)
    return grid


def fill_row(filling, *trailing):
    """Row where `filling` takes the free width and `trailing` stays its own size.

    A horizontal StackPanel never stretches its children, so a text box in one
    keeps a fixed width while the fields around it follow the window.
    """
    panel = DockPanel()
    panel.LastChildFill = True
    for control in reversed(trailing):
        DockPanel.SetDock(control, Dock.Right)
        panel.Children.Add(control)
    panel.Children.Add(filling)
    return panel


class FolderPicker(object):
    """A path box with a folder button, and optionally a 'use default' button.

    Every folder field in the extension is built from this so they share one
    look and one set of behaviours.  Add `control` to a layout and read or
    write the value through `path`.

    Args:
        value: initial path.
        pick_tooltip: hover text for the folder button.
        on_pick: called after the user picks a folder, for callers that react
            to a new path (rescanning a folder) without reacting to typing.
        on_default: returns the default path, or a falsy value to leave the
            box alone.  Supplying it is what adds the second button, so each
            field decides for itself what "default" means.
        default_tooltip: hover text for the default button.
        on_change: TextChanged handler, for callers that revalidate on typing.
    """

    def __init__(
        self,
        value="",
        pick_tooltip="Pick a folder",
        on_pick=None,
        on_default=None,
        default_tooltip="Use the default folder",
        on_change=None,
    ):
        self._on_pick = on_pick
        self._on_default = on_default
        self.textbox = textbox(value)
        if on_change:
            self.textbox.TextChanged += on_change

        buttons = [icon_button(FOLDER_GLYPH, pick_tooltip)]
        buttons[0].Click += self._pick
        if on_default:
            default = icon_button(DEFAULT_FOLDER_GLYPH, default_tooltip)
            default.Click += self._default
            buttons.append(default)
        self.control = fill_row(self.textbox, *buttons)

    def _get_path(self):
        return self.textbox.Text.strip()

    def _set_path(self, value):
        self.textbox.Text = value or ""

    path = property(_get_path, _set_path)

    def _pick(self, sender, args):
        from pyrevit import forms

        folder = forms.pick_folder()
        if not folder:
            return
        self.path = folder
        if self._on_pick:
            self._on_pick()

    def _default(self, sender, args):
        folder = self._on_default()
        if folder:
            self.path = folder
