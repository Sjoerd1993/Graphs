# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, Gtk

from graphs import calculation, graphs, ui, utilities
from graphs.item import Item

KEYS = [
    "addequation_equation", "addequation_step_size",
    "addequation_x_start", "addequation_x_stop",
]


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/add_equation_window.ui")
class AddEquationWindow(Adw.Window):
    __gtype_name__ = "AddEquationWindow"
    addequation_equation = Gtk.Template.Child()
    addequation_x_start = Gtk.Template.Child()
    addequation_x_stop = Gtk.Template.Child()
    addequation_step_size = Gtk.Template.Child()
    name = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application,
                         transient_for=application.main_window)
        ui.load_values_from_dict(self, {
            key: self.props.application.preferences[key] for key in KEYS
        })
        self.present()

    @Gtk.Template.Callback()
    def on_accept(self, _widget):
        """Launched when the accept button is pressed on the equation window"""
        values = ui.save_values_to_dict(self, KEYS)
        try:
            xdata, ydata = calculation.create_dataset(
                utilities.string_to_float(values["addequation_x_start"]),
                utilities.string_to_float(values["addequation_x_stop"]),
                values["addequation_equation"],
                utilities.string_to_float(values["addequation_step_size"]),
            )
            self.props.application.preferences.update(values)
            name = str(self.name.get_text())
            if name == "":
                name = f"Y = {values['addequation_equation']}"
            graphs.add_items(
                self.props.application,
                [Item(self.props.application, xdata, ydata, name)])
            self.destroy()
        except ValueError as error:
            self.toast_overlay.add_toast(Adw.Toast(title=error))
        except (NameError, SyntaxError, TypeError) as exception:
            toast = _("{error} - Unable to add data from equation").format(
                error=exception.__class__.__name__)
            self.toast_overlay.add_toast(Adw.Toast(title=toast))
            logging.exception(toast)
