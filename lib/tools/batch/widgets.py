# -*- coding: utf-8 -*-
"""Small WPF control factories shared by the batch option presenters."""

from System.Windows import Thickness
from System.Windows.Controls import CheckBox, ComboBox, StackPanel, TextBlock, TextBox


def text(value, width=None):
    control = TextBlock()
    control.Text = value
    if width:
        control.Width = width
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


def stack(*controls):
    panel = StackPanel()
    for control in controls:
        panel.Children.Add(control)
    return panel
