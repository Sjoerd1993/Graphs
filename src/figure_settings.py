# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, GObject, Gtk

from graphs import styles, ui


class FigureSettings(GObject.Object):
    __gtype_name__ = "FigureSettings"

    title = GObject.Property(type=str, default="")
    bottom_label = GObject.Property(type=str, default="")
    left_label = GObject.Property(type=str, default="")
    top_label = GObject.Property(type=str, default="")
    right_label = GObject.Property(type=str, default="")

    bottom_scale = GObject.Property(type=int, default=0)
    left_scale = GObject.Property(type=int, default=0)
    top_scale = GObject.Property(type=int, default=0)
    right_scale = GObject.Property(type=int, default=0)

    legend = GObject.Property(type=bool, default=True)
    legend_position = GObject.Property(type=int, default=0)
    use_custom_style = GObject.Property(type=bool, default=False)
    custom_style = GObject.Property(type=str, default="adwaita")

    min_bottom = GObject.Property(type=float, default=0)
    max_bottom = GObject.Property(type=float, default=1)
    min_left = GObject.Property(type=float, default=0)
    max_left = GObject.Property(type=float, default=10)
    min_top = GObject.Property(type=float, default=0)
    max_top = GObject.Property(type=float, default=1)
    min_right = GObject.Property(type=float, default=0)
    max_right = GObject.Property(type=float, default=10)

    min_selected = GObject.Property(type=float, default=0)
    max_selected = GObject.Property(type=float, default=0)

    @staticmethod
    def new(settings):
        return FigureSettings(
            bottom_scale=settings.get_enum("bottom-scale"),
            left_scale=settings.get_enum("left-scale"),
            right_scale=settings.get_enum("right-scale"),
            top_scale=settings.get_enum("top-scale"),
            title=settings.get_string("title"),
            bottom_label=settings.get_string("bottom-label"),
            left_label=settings.get_string("left-label"),
            top_label=settings.get_string("top-label"),
            right_label=settings.get_string("right-label"),
            legend=settings.get_boolean("legend"),
            use_custom_style=settings.get_boolean("use-custom-style"),
            legend_position=settings.get_enum("legend-position"),
            custom_style=settings.get_string("custom-style"),
        )

    @staticmethod
    def new_from_dict(dictionary: dict):
        return FigureSettings(**dictionary)

    def to_dict(self):
        return {key: self.get_property(key) for key in dir(self.props)}

    def get_limits(self) -> dict:
        return {key: self.get_property(key) for key in [
            "min_bottom", "max_bottom", "min_top", "max_top", "min_left",
            "max_left", "min_right", "max_right",
        ]}

    def set_limits(self, limits: dict):
        for key, value in limits.items():
            self.set_property(key, value)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/figure_settings.ui")
class FigureSettingsWindow(Adw.PreferencesWindow):
    __gtype_name__ = "FigureSettingsWindow"

    title = Gtk.Template.Child()
    bottom_label = Gtk.Template.Child()
    left_label = Gtk.Template.Child()
    top_label = Gtk.Template.Child()
    right_label = Gtk.Template.Child()
    bottom_scale = Gtk.Template.Child()
    left_scale = Gtk.Template.Child()
    top_scale = Gtk.Template.Child()
    right_scale = Gtk.Template.Child()
    legend = Gtk.Template.Child()
    legend_position = Gtk.Template.Child()
    use_custom_style = Gtk.Template.Child()
    custom_style = Gtk.Template.Child()
    min_left = Gtk.Template.Child()
    max_left = Gtk.Template.Child()
    min_bottom = Gtk.Template.Child()
    max_bottom = Gtk.Template.Child()
    min_right = Gtk.Template.Child()
    max_right = Gtk.Template.Child()
    min_top = Gtk.Template.Child()
    max_top = Gtk.Template.Child()

    no_data_message = Gtk.Template.Child()

    def __init__(self, application, highlighted=None):
        super().__init__(
            application=application, transient_for=application.main_window,
        )

        ui.bind_values_to_object(
            self.props.application.props.figure_settings, self,
            ignorelist=["custom_style", "min_selected", "max_selected"],
        )
        styles_ = sorted(styles.get_user_styles(application).keys())
        self.custom_style.set_model(Gtk.StringList.new(styles_))
        self.custom_style.set_selected(styles_.index(
            self.props.application.props.figure_settings.props.custom_style))

        self.hide_unused_axes_limits()
        self.no_data_message.set_visible(
            self.props.application.props.data.is_empty(),
        )
        if highlighted is not None:
            getattr(self, highlighted).grab_focus()
        self.present()

    def hide_unused_axes_limits(self):
        used_axes = [
            ["bottom", False],
            ["left", False],
            ["top", False],
            ["right", False],
        ]
        for item in self.props.application.props.data:
            for index in item.xposition * 2, 1 + item.yposition * 2:
                used_axes[index][1] = True
        for (direction, visible) in used_axes:
            getattr(self, f"min_{direction}").set_visible(visible)
            getattr(self, f"max_{direction}").set_visible(visible)

    @Gtk.Template.Callback()
    def on_close(self, *_args):
        self.props.application.props.view_clipboard.add()
        self.destroy()

    @Gtk.Template.Callback()
    def on_custom_style_select(self, comborow, _ignored):
        selected_style = comborow.get_selected_item().get_string()
        figure_settings = self.props.application.props.figure_settings
        if selected_style != figure_settings.props.custom_style:
            figure_settings.props.custom_style = selected_style
