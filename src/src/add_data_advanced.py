# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gtk, Adw

from . import graphs, utilities

def open_add_data_advanced_window(widget, _, self):
    """
    Open the window for adding a new dataset from file with custom settings
    """
    win = AddAdvancedWindow(self)
    button = win.open_advanced_confirm_button
    win.set_transient_for(self.props.active_window)
    win.set_modal(True)
    button.connect("clicked", on_accept, self, win)
    win.present()

def on_accept(widget, self, window):
    """
    Runs when the dataset is loaded, uses the selected settings in the window 
    to set the import settings during loading
    """
    import_settings = dict()
    import_settings["column_x"] = int(window.column_x.get_value())
    import_settings["column_y"] = int(window.column_y.get_value())
    import_settings["skip_rows"] = int(window.skip_rows.get_value())
    import_settings["separator"] = window.separator.get_selected_item().get_string()
    import_settings["delimiter"] = window.delimiter.get_text()
    import_settings["guess_headers"] = window.guess_headers.get_active()
    import_settings["name"] = window.name.get_text()
    graphs.open_file_dialog(widget, _, self, import_settings = import_settings)
    window.destroy()

@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/add_data_advanced.ui")
class AddAdvancedWindow(Adw.Window):
    __gtype_name__ = "AddAdvancedWindow"
    delimiter = Gtk.Template.Child()
    separator = Gtk.Template.Child()
    column_x = Gtk.Template.Child()
    name = Gtk.Template.Child()
    guess_headers = Gtk.Template.Child()
    column_y = Gtk.Template.Child()
    skip_rows = Gtk.Template.Child()
    open_advanced_confirm_button = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        config = parent.preferences.config
        self.skip_rows.set_value(int(config["import_skip_rows"]))
        self.column_y.set_value(int(config["import_column_y"]))
        self.column_x.set_value(int(config["import_column_x"]))
        self.delimiter.set_text(config["import_delimiter"])
        utilities.set_chooser(self.separator, config["import_separator"])
        self.guess_headers.set_active(config["guess_headers"])
        style_context = self.open_advanced_confirm_button.get_style_context()
        style_context.add_class("suggested-action")
