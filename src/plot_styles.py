# SPDX-License-Identifier: GPL-3.0-or-later
import os
import shutil
from pathlib import Path

from gi.repository import Adw, Gtk, GLib

from graphs import utilities, file_io, graphs

from matplotlib.lines import Line2D


def get_system_styles(self):
    path = os.path.join(self.modulepath, "styles")
    styles = {}
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            styles[Path(file).stem] = os.path.join(path, file)
    return styles


def get_user_styles(self):
    path = os.path.join(utilities.get_config_path(), "styles")
    if not os.path.exists(path):
        reset_user_styles(self)
    styles = {}
    for file in sorted(os.listdir(path)):
        if os.path.isfile(os.path.join(path, file)):
            styles[Path(file).stem] = os.path.join(path, file)
    if not styles:
        reset_user_styles(self)
        styles = get_user_styles(self)
    return styles


def reset_user_styles(self):
    user_path = os.path.join(utilities.get_config_path(), "styles")
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    os.chdir(user_path)
    for file in os.listdir(user_path):
        if os.path.isfile(os.path.join(user_path, file)):
            os.remove(file)
    for style, path in get_system_styles(self).items():
        shutil.copy(path, os.path.join(user_path, f"{style}.mplstyle"))


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/plot_styles.ui")
class PlotStylesWindow(Adw.Window):
    __gtype_name__ = "PlotStylesWindow"
    leaflet = Gtk.Template.Child()
    styles_box = Gtk.Template.Child()
    reset_button = Gtk.Template.Child()
    back_button = Gtk.Template.Child()
    style_name = Gtk.Template.Child()
    font_chooser = Gtk.Template.Child()
    linestyle = Gtk.Template.Child()
    linewidth = Gtk.Template.Child()
    markers = Gtk.Template.Child()
    markersize = Gtk.Template.Child()
    tick_direction = Gtk.Template.Child()
    minor_ticks = Gtk.Template.Child()
    major_tick_width = Gtk.Template.Child()
    minor_tick_width = Gtk.Template.Child()
    major_tick_length = Gtk.Template.Child()
    minor_tick_length = Gtk.Template.Child()
    tick_bottom = Gtk.Template.Child()
    tick_left = Gtk.Template.Child()
    tick_top = Gtk.Template.Child()
    tick_right = Gtk.Template.Child()
    show_grid = Gtk.Template.Child()
    grid_linewidth = Gtk.Template.Child()
    grid_transparency = Gtk.Template.Child()
    value_padding = Gtk.Template.Child()
    label_padding = Gtk.Template.Child()
    title_padding = Gtk.Template.Child()
    axis_width = Gtk.Template.Child()
    text_color = Gtk.Template.Child()
    tick_color = Gtk.Template.Child()
    axis_color = Gtk.Template.Child()
    grid_color = Gtk.Template.Child()
    background_color = Gtk.Template.Child()
    edge_color = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.set_transient_for(self.parent.main_window)
        self.styles = []
        self.style = None
        self.reload()
        self.reset_button.connect("clicked", self.reset)
        self.back_button.connect("clicked", self.back)
        self.connect("close-request", self.on_close)
        self.set_title("Plot Styles")

        # setup editor
        self.marker_dict = Line2D.markers.copy()
        self.marker_dict["none"] = "none"
        self.font_chooser.set_use_font(True)
        self.linewidth.set_range(0, 10)
        utilities.populate_chooser(
            self.markers, sorted(list(self.marker_dict.values())))
        self.markersize.set_range(0, 10)
        self.major_tick_width.set_range(0, 4)
        self.minor_tick_width.set_range(0, 4)
        self.major_tick_length.set_range(0, 20)
        self.minor_tick_length.set_range(0, 20)
        self.grid_linewidth.set_range(0, 4)
        self.grid_transparency.set_range(0, 1)
        self.value_padding.set_range(0, 40)
        self.label_padding.set_range(0, 40)
        self.title_padding.set_range(0, 40)
        self.axis_width.set_range(0, 4)

        # color actions
        self.color_buttons = [
            self.text_color,
            self.tick_color,
            self.axis_color,
            self.grid_color,
            self.background_color,
            self.edge_color,
        ]
        for button in self.color_buttons:
            button.connect("clicked", self.on_color_change)
            button.provider = Gtk.CssProvider()
            button.get_style_context().add_provider(
                button.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.present()

    def edit(self, _, style):
        self.style = file_io.get_style(get_user_styles(self.parent)[style])
        self.style["name"] = style
        try:
            self.load()
        except KeyError:
            return
        self.leaflet.navigate(1)
        self.back_button.set_visible(True)
        self.set_title(style)

    def back(self, _):
        self.apply()
        self.reload()
        self.style = None
        self.leaflet.navigate(0)
        self.back_button.set_visible(False)
        self.set_title("Plot Styles")
        graphs.reload(self.parent)

    def load(self):
        style = self.style

        self.style_name.set_text(style["name"])

        # font
        font_description = self.font_chooser.get_font_desc().from_string(
            f"{style['font.sans-serif']} {style['font.size']}")
        self.font_chooser.set_font_desc(font_description)

        # lines
        utilities.set_chooser(self.linestyle, style["lines.linestyle"])
        self.linewidth.set_value(float(style["lines.linewidth"]))
        utilities.set_chooser(
            self.markers, self.marker_dict[style["lines.marker"]])
        self.markersize.set_value(float(style["lines.markersize"]))

        # ticks
        utilities.set_chooser(self.tick_direction, style["xtick.direction"])
        self.minor_ticks.set_active(style["xtick.minor.visible"] == "True")
        self.major_tick_width.set_value(float(style["xtick.major.width"]))
        self.minor_tick_width.set_value(float(style["xtick.minor.width"]))
        self.major_tick_length.set_value(float(style["xtick.major.size"]))
        self.minor_tick_length.set_value(float(style["xtick.minor.size"]))
        self.tick_bottom.set_active(style["xtick.bottom"] == "True")
        self.tick_left.set_active(style["ytick.left"] == "True")
        self.tick_top.set_active(style["xtick.top"] == "True")
        self.tick_right.set_active(style["ytick.right"] == "True")

        # grid
        self.show_grid.set_active(style["axes.grid"] == "True")
        self.grid_linewidth.set_value(float(style["grid.linewidth"]))
        self.grid_transparency.set_value(1 - float(style["grid.alpha"]))

        # padding
        self.value_padding.set_value(float(style["xtick.major.pad"]))
        self.label_padding.set_value(float(style["axes.labelpad"]))
        self.title_padding.set_value(float(style["axes.titlepad"]))

        # colors
        self.text_color.color = style["text.color"]
        self.tick_color.color = style["xtick.color"]
        self.axis_color.color = style["axes.edgecolor"]
        self.grid_color.color = style["grid.color"]
        self.background_color.color = style["axes.facecolor"]
        self.edge_color.color = style["figure.facecolor"]

        for button in self.color_buttons:
            button.provider.load_from_data(
                f"button {{ color: #{button.color}; }}", -1)

        # other
        self.axis_width.set_value(float(style["axes.linewidth"]))

    def apply(self):
        style = self.style

        # font
        font_description = self.font_chooser.get_font_desc()
        style["font.sans-serif"] = font_description.get_family()
        font_name = font_description.to_string().lower().split(" ")
        style["font.style"] = utilities.get_font_style(font_name)
        font_weight = utilities.get_font_weight(font_name)
        style["font.weight"] = font_weight
        style["axes.titleweight"] = font_weight
        style["axes.labelweight"] = font_weight
        style["figure.titleweight"] = font_weight
        style["figure.labelweight"] = font_weight
        font_size = font_name[-1]
        style["font.size"] = font_size
        style["axes.labelsize"] = font_size
        style["xtick.labelsize"] = font_size
        style["ytick.labelsize"] = font_size
        style["axes.titlesize"] = font_size
        style["legend.fontsize"] = font_size
        style["figure.titlesize"] = font_size
        style["figure.labelsize"] = font_size

        # lines
        style["lines.linestyle"] = \
            self.linestyle.get_selected_item().get_string()
        style["lines.linewidth"] = self.linewidth.get_value()
        style["lines.marker"] = utilities.get_dict_by_value(
            self.marker_dict, self.markers.get_selected_item().get_string())
        style["lines.markersize"] = self.markersize.get_value()

        # ticks
        tick_direction = self.tick_direction.get_selected_item().get_string()
        style["xtick.direction"] = tick_direction
        style["ytick.direction"] = tick_direction
        minor_ticks = self.minor_ticks.get_active()
        style["xtick.minor.visible"] = minor_ticks
        style["ytick.minor.visible"] = minor_ticks
        style["xtick.major.width"] = self.major_tick_width.get_value()
        style["ytick.major.width"] = self.major_tick_width.get_value()
        style["xtick.minor.width"] = self.minor_tick_width.get_value()
        style["ytick.minor.width"] = self.minor_tick_width.get_value()
        style["xtick.major.size"] = self.major_tick_length.get_value()
        style["ytick.major.size"] = self.major_tick_length.get_value()
        style["xtick.minor.size"] = self.minor_tick_length.get_value()
        style["ytick.minor.size"] = self.minor_tick_length.get_value()
        style["xtick.bottom"] = self.tick_bottom.get_active()
        style["ytick.left"] = self.tick_left.get_active()
        style["xtick.top"] = self.tick_top.get_active()
        style["ytick.right"] = self.tick_right.get_active()

        # grid
        style["axes.grid"] = self.show_grid.get_active()
        style["grid.linewidth"] = self.grid_linewidth.get_value()
        style["grid.alpha"] = 1 - self.grid_transparency.get_value()

        # padding
        style["xtick.major.pad"] = self.value_padding.get_value()
        style["xtick.minor.pad"] = self.value_padding.get_value()
        style["ytick.major.pad"] = self.value_padding.get_value()
        style["ytick.minor.pad"] = self.value_padding.get_value()
        style["axes.labelpad"] = self.label_padding.get_value()
        style["axes.titlepad"] = self.title_padding.get_value()

        # colors
        style["text.color"] = self.text_color.color
        style["axes.labelcolor"] = self.text_color.color
        style["xtick.color"] = self.tick_color.color
        style["ytick.color"] = self.tick_color.color
        style["axes.edgecolor"] = self.axis_color.color
        style["grid.color"] = self.grid_color.color
        style["axes.facecolor"] = self.background_color.color
        style["figure.facecolor"] = self.edge_color.color
        style["figure.edgecolor"] = self.edge_color.color

        # other
        style["axes.linewidth"] = self.axis_width.get_value()

        # name & save
        styles_path = os.path.join(utilities.get_config_path(), "styles")
        os.remove(os.path.join(styles_path, f"{style['name']}.mplstyle"))
        style["name"] = self.style_name.get_text()
        file_io.write_style(
            os.path.join(styles_path, f"{style['name']}.mplstyle"), style)

    def delete(self, _, style):
        os.remove(get_user_styles(self.parent)[style])
        self.reload()

    def copy(self, _, style):
        loop = True
        i = 0
        while loop:
            i += 1
            new_style = f"{style} ({i})"
            loop = False
            for style_1 in get_user_styles(self.parent).keys():
                if new_style == style_1:
                    loop = True
        user_path = os.path.join(utilities.get_config_path(), "styles")
        shutil.copy(
            os.path.join(user_path, f"{style}.mplstyle"),
            os.path.join(user_path, f"{new_style}.mplstyle"))
        self.reload()

    def reset(self, _):
        reset_user_styles(self.parent)
        self.reload()

    def reload(self):
        for box in self.styles.copy():
            self.styles.remove(box)
            self.styles_box.remove(self.styles_box.get_row_at_index(0))
        for style in get_user_styles(self.parent).keys():
            box = StyleBox(self, style)
            self.styles.append(box)
            self.styles_box.append(box)

    def on_close(self, _):
        if self.style is not None:
            self.apply()
        graphs.reload(self.parent)
        self.destroy()

    def on_color_change(self, button):
        color = utilities.hex_to_rgba(f"#{button.color}")
        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(
            self.parent.main_window, color, None, self.on_color_change_accept,
            button)

    def on_color_change_accept(self, dialog, result, button):
        try:
            color = dialog.choose_rgba_finish(result)
            if color is not None:
                color_hex = utilities.rgba_to_hex(color)
                button.provider.load_from_data(
                    f"button {{ color: {color_hex}; }}", -1)
                button.color = color_hex.replace("#", "")
        except GLib.GError:
            pass


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_box.ui")
class StyleBox(Gtk.Box):
    __gtype_name__ = "StyleBox"
    label = Gtk.Template.Child()
    copy_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()

    def __init__(self, parent, style):
        super().__init__()
        self.label.set_label(utilities.shorten_label(style, 50))
        self.copy_button.connect("clicked", parent.copy, style)
        self.delete_button.connect("clicked", parent.delete, style)
        self.edit_button.connect("clicked", parent.edit, style)
