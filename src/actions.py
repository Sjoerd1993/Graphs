# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
import logging
from gettext import gettext as _

from gi.repository import Adw

from graphs import clipboard, graphs, operations, ui
from graphs.add_data_advanced import AddAdvancedWindow
from graphs.add_equation import AddEquationWindow
from graphs.export_figure import ExportFigureWindow
from graphs.misc import InteractionMode
from graphs.plot_settings import PlotSettingsWindow
from graphs.plot_styles import PlotStylesWindow
from graphs.preferences import PreferencesWindow
from graphs.transform_data import TransformWindow


def toggle_sidebar(_action, _shortcut, self):
    flap = self.main_window.sidebar_flap
    flap.set_reveal_flap(not flap.get_reveal_flap())


def quit_action(_action, _target, self):
    self.quit()


def about_action(_action, _target, self):
    ui.show_about_window(self)


def preferences_action(_action, _target, self):
    PreferencesWindow(self)


def plot_settings_action(_action, _target, self):
    PlotSettingsWindow(self)


def add_data_action(_action, _target, self):
    ui.add_data_dialog(self)


def add_data_advanced_action(_action, _target, self):
    AddAdvancedWindow(self)


def add_equation_action(_action, _target, self):
    AddEquationWindow(self)


def select_all_action(_action, _target, self):
    if not self.datadict:
        return
    for item in self.datadict.values():
        item.selected = True
    graphs.refresh(self)
    ui.reload_item_menu(self)
    ui.enable_data_dependent_buttons(self)


def select_none_action(_action, _target, self):
    if not self.datadict:
        return
    for item in self.datadict.values():
        item.selected = False
    graphs.refresh(self)
    ui.reload_item_menu(self)
    ui.enable_data_dependent_buttons(self)


def undo_action(_action, _target, self):
    clipboard.undo(self)


def redo_action(_action, _target, self):
    clipboard.redo(self)


def restore_view_action(_action, _target, self):
    graphs.reload(self)


def view_back_action(_action, _target, self):
    self.canvas.dummy_toolbar.back()


def view_forward_action(_action, _target, self):
    self.canvas.dummy_toolbar.forward()


def export_data_action(_action, _target, self):
    ui.export_data_dialog(self)


def export_figure_action(_action, _target, self):
    ExportFigureWindow(self)


def plot_styles_action(_action, _target, self):
    PlotStylesWindow(self)


def save_project_action(_action, _target, self):
    ui.save_project_dialog(self)


def open_project_action(_action, _target, self):
    if len(self.datadict) > 0:
        def on_response(_dialog, response):
            if response == "discard":
                ui.open_project_dialog(self)
        heading = _("Discard Data?")
        body = _("Opening a project will discard all open data.")
        dialog = Adw.MessageDialog.new(
            self.main_window, heading, body)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("discard", _("Discard"))
        dialog.set_close_response("cancel")
        dialog.set_default_response("discard")
        dialog.set_response_appearance(
            "discard", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response)
        dialog.present()
        return
    ui.open_project_dialog(self)


def delete_selected_action(_action, _target, self):
    for item in self.datadict.values():
        if item.selected:
            graphs.delete_item(self, item.key, True)


def translate_x_action(_action, _target, self):
    win = self.main_window
    try:
        offset = eval(win.translate_x_entry.get_text())
    except ValueError as exception:
        message = _("{error}: Unable to do translation, \
make sure to enter a valid number").format(error=exception.__class__.__name__)
        win.add_toast(message)
        logging.exception(message)
        offset = 0
    operations.perform_operation(self, operations.translate_x, offset)


def translate_y_action(_action, _target, self):
    win = self.main_window
    try:
        offset = eval(win.translate_y_entry.get_text())
    except ValueError as exception:
        message = _("{error}: Unable to do translation, \
make sure to enter a valid number").format(error=exception.__class__.__name__)
        win.add_toast(message)
        logging.exception(message)
        offset = 0
    operations.perform_operation(self, operations.translate_y, offset)


def multiply_x_action(_action, _target, self):
    win = self.main_window
    try:
        multiplier = eval(win.multiply_x_entry.get_text())
    except ValueError as exception:
        message = _("{error}: Unable to do translation, \
make sure to enter a valid number").format(error=exception.__class__.__name__)
        win.add_toast(message)
        logging.exception(message)
        multiplier = 1
    operations.perform_operation(self, operations.multiply_x, multiplier)


def multiply_y_action(_action, _target, self):
    win = self.main_window
    try:
        multiplier = eval(win.multiply_y_entry.get_text())
    except ValueError as exception:
        message = _("{error}: Unable to do translation, \
make sure to enter a valid number").format(error=exception.__class__.__name__)
        win.add_toast(message)
        logging.exception(message)
        multiplier = 1
    operations.perform_operation(self, operations.multiply_y, multiplier)


def normalize_action(_action, _target, self):
    operations.perform_operation(self, operations.normalize)


def smoothen_action(_action, _target, self):
    operations.perform_operation(self, operations.smoothen)


def center_action(_action, _target, self):
    operations.perform_operation(
        self, operations.center,
        self.preferences.config["action_center_data"])


def shift_vertically_action(_action, _target, self):
    operations.perform_operation(
        self, operations.shift_vertically,
        self.plot_settings.yscale, self.plot_settings.right_scale,
        self.datadict)


def combine_action(_action, _target, self):
    operations.combine(self)


def cut_selected_action(_action, _target, self):
    if self.interaction_mode == InteractionMode.SELECT:
        operations.perform_operation(self, operations.cut_selected)


def get_derivative_action(_action, _target, self):
    operations.perform_operation(self, operations.get_derivative)


def get_integral_action(_action, _target, self):
    operations.perform_operation(self, operations.get_integral)


def get_fourier_action(_action, _target, self):
    operations.perform_operation(self, operations.get_fourier)


def get_inverse_fourier_action(_action, _target, self):
    operations.perform_operation(self, operations.get_inverse_fourier)


def transform_action(_action, _target, self):
    win = TransformWindow(self)
    win.present()
