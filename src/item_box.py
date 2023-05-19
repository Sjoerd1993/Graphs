# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import GLib, Gdk, Gtk

from graphs import clipboard, graphs, ui, utilities
from graphs.edit_item import EditItemWindow


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/item_box.ui")
class ItemBox(Gtk.Box):
    __gtype_name__ = "ItemBox"
    label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()
    color_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()

    def __init__(self, parent, item):
        super().__init__()
        self.item = item
        self.label.set_text(utilities.shorten_label(item.name))
        self.check_button.set_active(item.selected)
        self.parent = parent

        self.gesture = Gtk.GestureClick()
        self.gesture.set_button(0)
        self.add_controller(self.gesture)
        self.edit_button.connect("clicked", self.edit)
        self.color_button.connect("clicked", self.choose_color)
        self.delete_button.connect("clicked", self.delete)
        self.check_button.connect("toggled", self.on_toggle)
        self.provider = Gtk.CssProvider()
        self.color_button.get_style_context().add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.update_color()
        self.drag_source = Gtk.DragSource.new()
        self.drag_source.set_actions(Gdk.DragAction.COPY)
        self.drag_source.connect("prepare", self.on_dnd_prepare)
        self.drop_source = Gtk.DropTarget.new(str, Gdk.DragAction.COPY)
        self.drop_source.key = item.key
        self.drop_source.connect("drop", self.on_dnd_drop)

        self.add_controller(self.drag_source)
        self.add_controller(self.drop_source)

    def on_dnd_drop(self, drop_target, value, _x, _y):
        # Handle the dropped data here
        self.parent.datadict
        self.parent.datadict = utilities.change_key_position(
            self.parent.datadict, drop_target.key, value)
        ui.reload_item_menu(self.parent)
        clipboard.add(self.parent)
        graphs.reload(self.parent, reset_limits=False)

    def on_dnd_prepare(self, drag_source, x, y):
        snapshot = Gtk.Snapshot.new()
        self.do_snapshot(self, snapshot)
        paintable = snapshot.to_paintable()
        drag_source.set_icon(paintable, int(x), int(y))

        data = self.item.key
        return Gdk.ContentProvider.new_for_value(data)

    def update_color(self):
        self.provider.load_from_data(
            f"button {{ color: {self.item.color}; }}", -1)

    def choose_color(self, _):
        color = utilities.hex_to_rgba(self.item.color)
        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(
            self.parent.main_window, color, None, self.on_color_dialog_accept)

    def on_color_dialog_accept(self, dialog, result):
        try:
            color = dialog.choose_rgba_finish(result)
            if color is not None:
                self.item.color = utilities.rgba_to_hex(color).upper()
                self.update_color()
                clipboard.add(self.parent)
                graphs.refresh(self.parent)
        except GLib.GError:
            pass

    def delete(self, _):
        graphs.delete_item(self.parent, self.item.key, True)

    def on_toggle(self, _):
        self.item.selected = self.check_button.get_active()
        graphs.refresh(self.parent, False)
        ui.enable_data_dependent_buttons(self.parent)

    def edit(self, _):
        EditItemWindow(self.parent, self.item)
