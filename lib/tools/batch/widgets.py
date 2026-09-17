# -*- coding: utf-8 -*-
"""Small WPF control factories shared by the batch option presenters."""

import clr

clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
clr.AddReference("WindowsBase")

from System.Windows import FontWeights, Thickness, VerticalAlignment
from System.Windows.Media import FontFamily
from System.Windows.Controls import (
    Button,
    CheckBox,
    ComboBox,
    Dock,
    DockPanel,
    Orientation,
    StackPanel,
    TextBlock,
    TextBox,
)


def text(value, width=None, bold=False, centered=False):
    control = TextBlock()
    control.Text = value
    if width:
        control.Width = width
    if bold:
        control.FontWeight = FontWeights.Bold
    if centered:
        control.VerticalAlignment = VerticalAlignment.Center
    return control


def label(value):
    control = text(value)
    control.Margin = Thickness(0, 8, 0, 2)
    return control


def checkbox(content="", checked=False, width=None):
    control = CheckBox()
    control.Content = content
    control.IsChecked = checked
    if width:
        control.Width = width
    return control


def textbox(text="", width=None):
    control = TextBox()
    control.Text = text
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
