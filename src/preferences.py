# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, Gio, Gtk

from graphs import file_io, graphs, misc, plot_styles, ui, utilities


MIGRATION_KEYS = {
    # new: old
    "other_handle_duplicates": "handle_duplicates",
    "other_hide_unselected": "hide_unselected",
}


def _validate(config: dict, template: dict):
    """
    Validates a given dictionary against a template, such that they
    remain compatible with updated versions of Graphs. If the key in the
    dictionary is not present in the template due to an update, the key will
    be updated using MIGRATION_KEYS.

    If the template or validated key does not match with the MIGRATION_KEYS,
    the template keys and their associated values will be used instead for
    the validated dictionary.

    Args:
        config: Dictionary to be validated
        template: Template dictionary to which the config is validated against
    Returns:
        dict: Validated dictionary
    """
    return {key: config[key if key in config else MIGRATION_KEYS[key]]
            if key in config
            or (key in MIGRATION_KEYS and MIGRATION_KEYS[key] in config)
            else value for key, value in template.items()}


class Preferences(dict):
    def __init__(self):
        config_dir = utilities.get_config_directory()
        if not config_dir.query_exists(None):
            config_dir.make_directory_with_parents(None)
        config_file = config_dir.get_child_for_display_name("config.json")
        import_file = config_dir.get_child_for_display_name("import.json")
        template_config_file = Gio.File.new_for_uri(
            "resource:///se/sjoerd/Graphs/config.json")
        template_import_file = Gio.File.new_for_uri(
            "resource:///se/sjoerd/Graphs/import.json")
        if not config_file.query_exists(None):
            template_config_file.copy(
                config_file, Gio.FileCopyFlags(1), None, None, None)
            logging.info(_("New configuration file created"))
        if not import_file.query_exists(None):
            template_import_file.copy(
                import_file, Gio.FileCopyFlags(1), None, None, None)
            logging.info(_("New Import Settings file created"))

        super().update(_validate(
            file_io.parse_json(config_file),
            file_io.parse_json(template_config_file)))

        import_params_template = file_io.parse_json(template_import_file)
        self["import_params"] = _validate({
            key: _validate(item, import_params_template[key])
            for key, item in file_io.parse_json(import_file).items()
        }, import_params_template)

    def update(self, values):
        super().update(values)
        self.save()

    def save(self):
        config_dir = utilities.get_config_directory()
        config = self.copy()
        file_io.write_json(
            config_dir.get_child_for_display_name("import.json"),
            config["import_params"])
        del config["import_params"]
        file_io.write_json(
            config_dir.get_child_for_display_name("config.json"),
            config)


CONFIG_WHITELIST = [
    "action_center_data", "other_handle_duplicates", "other_hide_unselected",
    "override_style_change", "plot_title", "plot_x_label", "plot_y_label",
    "plot_top_label", "plot_right_label", "plot_x_scale", "plot_y_scale",
    "plot_top_scale", "plot_right_scale", "plot_x_position", "plot_y_position",
    "plot_legend", "plot_legend_position", "plot_use_custom_style",
    "plot_custom_style",
]


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/preferences.ui")
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"
    action_center_data = Gtk.Template.Child()
    other_handle_duplicates = Gtk.Template.Child()
    other_hide_unselected = Gtk.Template.Child()
    override_style_change = Gtk.Template.Child()
    plot_title = Gtk.Template.Child()
    plot_x_label = Gtk.Template.Child()
    plot_y_label = Gtk.Template.Child()
    plot_top_label = Gtk.Template.Child()
    plot_right_label = Gtk.Template.Child()
    plot_x_scale = Gtk.Template.Child()
    plot_y_scale = Gtk.Template.Child()
    plot_top_scale = Gtk.Template.Child()
    plot_right_scale = Gtk.Template.Child()
    plot_x_position = Gtk.Template.Child()
    plot_y_position = Gtk.Template.Child()
    plot_legend = Gtk.Template.Child()
    plot_legend_position = Gtk.Template.Child()
    plot_use_custom_style = Gtk.Template.Child()
    plot_custom_style = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application,
                         transient_for=application.main_window)

        utilities.populate_chooser(
            self.import_separator, misc.SEPARATORS, translate=False)
        utilities.populate_chooser(
            self.action_center_data, misc.ACTION_CENTER_DATA)
        utilities.populate_chooser(
            self.other_handle_duplicates, misc.HANDLE_DUPLICATES)
        utilities.populate_chooser(self.plot_x_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_y_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_top_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_right_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_x_position, misc.X_POSITIONS)
        utilities.populate_chooser(self.plot_y_position, misc.Y_POSITIONS)
        utilities.populate_chooser(
            self.plot_legend_position, misc.LEGEND_POSITIONS)

        utilities.populate_chooser(
            self.plot_custom_style,
            plot_styles.get_user_styles(self.props.application).keys(),
            translate=False)
        self.load()
        self.present()

    def load(self):
        ui.load_values_from_dict(
            self, {key: self.props.application.preferences[key]
                   for key in CONFIG_WHITELIST})
        columns_params = \
            self.props.application.preferences["import_params"]["columns"]
        self.import_delimiter.set_text(columns_params["delimiter"])
        utilities.set_chooser(
            self.import_separator, columns_params["separator"])
        self.import_column_x.set_value(columns_params["column_x"])
        self.import_column_y.set_value(columns_params["column_y"])
        self.import_skip_rows.set_value(columns_params["skip_rows"])

    def apply(self):
        # to be removed
        columns_params = \
            self.props.application.preferences["import_params"]["columns"]
        columns_params["delimiter"] = self.import_delimiter.get_text()
        columns_params["separator"] = \
            utilities.get_selected_chooser_item(self.import_separator)
        columns_params["column_x"] = int(self.import_column_x.get_value())
        columns_params["column_y"] = int(self.import_column_y.get_value())
        columns_params["skip_rows"] = int(self.import_skip_rows.get_value())

        self.props.application.preferences.update(ui.save_values_to_dict(
            self, CONFIG_WHITELIST))

    @Gtk.Template.Callback()
    def on_close(self, _):
        self.apply()
        graphs.refresh(self.props.application)
