// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;
using Adw;

namespace Graphs {
    /**
     * Main window
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/window.ui")]
    public class Window : Adw.ApplicationWindow {

        [GtkChild]
        private unowned Button undo_button { get; }

        [GtkChild]
        private unowned Button redo_button { get; }

        [GtkChild]
        private unowned Button view_back_button { get; }

        [GtkChild]
        private unowned Button view_forward_button { get; }

        [GtkChild]
        private unowned MenuButton view_menu_button { get; }

        [GtkChild]
        private unowned ToggleButton pan_button { get; }

        [GtkChild]
        private unowned ToggleButton zoom_button { get; }

        [GtkChild]
        private unowned ToggleButton select_button { get; }

        [GtkChild]
        private unowned ListBox item_list { get; }

        [GtkChild]
        public unowned Adw.OverlaySplitView overlay_split_view { get; }

        [GtkChild]
        private unowned Adw.ToastOverlay toast_overlay { get; }

        [GtkChild]
        private unowned Adw.HeaderBar content_headerbar { get; }

        [GtkChild]
        private unowned Adw.HeaderBar content_footerbar { get; }

        [GtkChild]
        protected unowned Adw.WindowTitle content_title { get; }

        [GtkChild]
        private unowned Overlay drag_overlay { get; }

        [GtkChild]
        private unowned Revealer drag_revealer { get; }

        [GtkChild]
        private unowned Adw.Bin operations_bin { get; }

        [GtkChild]
        private unowned Stack itemlist_stack { get; }

        public Data data { get; construct set; }

        protected CssProvider headerbar_provider { get; private set; }

        public int mode {
            set {
                pan_button.set_active (value == 0);
                zoom_button.set_active (value == 1);
                select_button.set_active (value == 2);
            }
            get {
                if (pan_button.get_active ()) return 0;
                if (zoom_button.get_active ()) return 1;
                if (select_button.get_active ()) return 2;
                return -1;
            }
        }

        public Canvas canvas {
            get { return toast_overlay.get_child () as Canvas; }
            set {
                value.bind_property ("mode", this, "mode", 2);
                toast_overlay.set_child (value);
                value.grab_focus ();
            }
        }

        protected Operations operations {
            get { return operations_bin.get_child () as Operations; }
            private set { operations_bin.set_child (value); }
        }

        private bool _force_close = false;
        private uint _inhibit_cookie = 0;

        construct {
            this.headerbar_provider = new CssProvider ();
            content_headerbar.get_style_context ().add_provider (
                headerbar_provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );
            content_footerbar.get_style_context ().add_provider (
                headerbar_provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );

            var item_drop_target = new Gtk.DropTarget (typeof (Adw.ActionRow), Gdk.DragAction.MOVE);
            item_drop_target.drop.connect ((drop, val, x, y) => {
                var value_row = val.get_object () as ItemBox?;
                var target_row = item_list.get_row_at_y ((int) y) as ItemBox?;
                // If value or the target row is null, do not accept the drop
                if (value_row == null || target_row == null) {
                    return false;
                }

                target_row.change_position (value_row.get_index ());
                target_row.set_state_flags (Gtk.StateFlags.NORMAL, true);

                return true;
            });
            item_list.add_controller (item_drop_target);

            var file_drop_target = new Gtk.DropTarget (typeof (Gdk.FileList), Gdk.DragAction.COPY);
            file_drop_target.notify["current-drop"].connect (() => {
                bool reveal = file_drop_target.current_drop != null;
                drag_revealer.reveal_child = reveal;
                if (reveal) {
                    drag_overlay.child.add_css_class ("blurred");
                } else {
                    drag_overlay.child.remove_css_class ("blurred");
                }
            });
            file_drop_target.drop.connect ((drop, val, x, y) => {
                var application = application as Application;
                var file_list = ((Gdk.FileList) val).get_files ();
                File[] files = {};
                for (uint i = 0; i < file_list.length (); i++) {
                    files += file_list.nth_data (i);
                }
                application.python_helper.import_from_files (this, files);
            });
            drag_overlay.add_controller (file_drop_target);

            string path = "/se/sjoerd/Graphs/ui/window-shortcuts.ui";
            var builder = new Builder.from_resource (path);
            set_help_overlay (builder.get_object ("help_overlay") as ShortcutsWindow);
        }

        protected void setup () {
            var application = application as Application;

            Actions.setup (application, this);

            this.operations = new Operations (this);

            data.bind_property ("can_undo", undo_button, "sensitive", 2);
            data.bind_property ("can_redo", redo_button, "sensitive", 2);
            data.bind_property ("can_view_back", view_back_button, "sensitive", 2);
            data.bind_property ("can_view_forward", view_forward_button, "sensitive", 2);

            data.items_changed.connect (on_items_changed);
            data.selection_changed.connect (on_selection_changed);

            // Inhibit session end when there is unsaved data present
            data.notify["unsaved"].connect (() => {
                if (data.unsaved) {
                    application.inhibit (
                        this,
                        ApplicationInhibitFlags.LOGOUT,
                        content_title.get_title ()
                    );
                } else if (_inhibit_cookie > 0) {
                    application.uninhibit (_inhibit_cookie);
                }
            });

            on_items_changed ();
            if (application.debug) {
                add_css_class ("devel");
                set_title (_("Graphs (Development)"));
            }
        }

        private void on_items_changed () {
            update_view_menu ();
            item_list.remove_all ();
            var export_data_action = lookup_action ("export_data") as SimpleAction;
            var optimize_limits_action = lookup_action ("optimize_limits") as SimpleAction;
            if (data.is_empty ()) {
                itemlist_stack.get_pages ().select_item (0, true);
                operations.shift_button.set_sensitive (false);
                operations.smoothen_button.set_sensitive (false);
                operations.set_cut_sensitivity (false);
                operations.set_entry_sensitivity (false);
                export_data_action.set_enabled (false);
                optimize_limits_action.set_enabled (false);
                return;
            }
            itemlist_stack.get_pages ().select_item (1, true);
            bool items_selected = false;
            bool data_items_selected = false;
            uint index = 0;
            foreach (Item item in data) {
                string typename = item.get_type ().name ();
                bool data_item = typename == "GraphsDataItem" || typename == "GraphsGeneratedDataItem";
                item_list.append (create_box_for_item (item, index, data_item));

                items_selected = items_selected || item.selected;
                data_items_selected = data_items_selected || (item.selected && data_item);
                index++;
            }
            operations.shift_button.set_sensitive (items_selected);
            operations.smoothen_button.set_sensitive (data_items_selected);
            operations.set_cut_sensitivity (data_items_selected && select_button.get_active ());
            operations.set_entry_sensitivity (items_selected);
            export_data_action.set_enabled (items_selected);
            optimize_limits_action.set_enabled (true);
        }

        private void on_selection_changed () {
            var export_data_action = lookup_action ("export_data") as SimpleAction;
            if (data.is_empty ()) {
                operations.shift_button.set_sensitive (false);
                operations.smoothen_button.set_sensitive (false);
                operations.set_cut_sensitivity (false);
                operations.set_entry_sensitivity (false);
                export_data_action.set_enabled (false);
                return;
            }
            bool items_selected = false;
            bool data_items_selected = false;
            foreach (Item item in data) {
                string typename = item.get_type ().name ();
                bool data_item = typename == "GraphsDataItem" || typename == "GraphsGeneratedDataItem";

                items_selected = items_selected || item.selected;
                data_items_selected = data_items_selected || (item.selected && data_item);
                if (items_selected && data_items_selected) break;
            }
            operations.shift_button.set_sensitive (items_selected);
            operations.smoothen_button.set_sensitive (data_items_selected);
            operations.set_cut_sensitivity (data_items_selected && select_button.get_active ());
            operations.set_entry_sensitivity (items_selected);
            export_data_action.set_enabled (items_selected);
        }

        private ItemBox create_box_for_item (Item item, uint index, bool is_data_item) {
            var row = new ItemBox (this, item, index);
            row.setup_interactions (is_data_item);

            double drag_x = 0.0;
            double drag_y = 0.0;

            var drop_controller = new Gtk.DropControllerMotion ();
            var drag_source = new Gtk.DragSource () {
                actions = Gdk.DragAction.MOVE
            };

            row.add_controller (drag_source);
            row.add_controller (drop_controller);

            // Drag handling
            drag_source.prepare.connect ((x, y) => {
                drag_x = x;
                drag_y = y;

                Value val = Value (typeof (Adw.ActionRow));
                val.set_object (row);

                return new Gdk.ContentProvider.for_value (val);
            });

            drag_source.drag_begin.connect ((drag) => {
                var drag_widget = new Gtk.ListBox ();
                drag_widget.set_size_request (row.get_width (), row.get_height ());
                drag_widget.add_css_class ("boxed-list");

                var drag_row = new ItemBox (this, item, index);

                drag_widget.append (drag_row);
                drag_widget.drag_highlight_row (drag_row);

                var icon = Gtk.DragIcon.get_for_drag (drag) as Gtk.DragIcon;
                icon.child = drag_widget;

                drag.set_hotspot ((int) drag_x, (int) drag_y);
            });

            // Update row visuals during DnD operation
            drop_controller.enter.connect (() => item_list.drag_highlight_row (row));
            drop_controller.leave.connect (() => item_list.drag_unhighlight_row ());

            return row;
        }

        /**
         * Add a toast to the window.
         */
        public void add_toast (Adw.Toast toast) {
            toast_overlay.add_toast (toast);
        }

        /**
         * Add a toast to the window.
         *
         * The toast is created automatically with the given title.
         */
        public void add_toast_string (string title) {
            add_toast (new Adw.Toast (title));
        }

        /**
         * Add a toast to the window.
         *
         * The toast is created automatically with the given title.
         * An action is automatically created, to open the containing folder
         * of file.
         */
        public void add_toast_string_with_file (string title, File file) {
            SimpleAction action = new SimpleAction ("open-file-location", null);
            action.activate.connect (() => {
                Tools.open_file_location (file);
            });
            add_action (action);
            add_toast (new Adw.Toast (title) {
                button_label = _("Open Location"),
                action_name = "win.open-file-location"
            });
        }

        /**
         * Add Toast with undo action.
         */
        public void add_undo_toast (string title) {
            add_toast (new Adw.Toast (title) {
                button_label = _("Undo"),
                action_name = "win.undo"
            });
        }

        /**
         * Repopulate the view menu
         */
        public void update_view_menu () {
            var view_menu = new Menu ();
            Menu optimize_section = new Menu ();
            optimize_section.append_item (
                new MenuItem (_("Optimize Limits"), "win.optimize_limits")
            );
            view_menu.append_section (null, optimize_section);

            string[] scale_names = {
                C_("scale", "Linear"),
                C_("scale", "Logarithmic (Base 10)"),
                C_("scale", "Logarithmic (Base 2)"),
                C_("scale", "Radians"),
                C_("scale", "Square Root"),
                C_("scale", "Inverse Root")
            };

            Menu scales_section = new Menu ();
            bool[] visible_axes = data.get_used_positions ();
            bool both_x = visible_axes[0] && visible_axes[1];
            bool both_y = visible_axes[2] && visible_axes[3];
            for (int i = 0; i < DIRECTION_NAMES.length; i++) {
                if (!visible_axes[i]) continue;
                string direction = DIRECTION_NAMES[i];
                Menu scale_section = new Menu ();
                for (int j = 0; j < scale_names.length; j++) {
                    string scale = scale_names[j];
                    MenuItem scale_item = new MenuItem (
                        scale, @"win.change-$direction-scale"
                    );
                    scale_item.set_attribute_value (
                        "target",
                        new Variant.string (j.to_string ())
                    );
                    scale_section.append_item (scale_item);
                }
                string label;
                if (i < 2) {
                    if (both_x) {
                        if (i == 0) label = _("Bottom X Axis Scale");
                        else label = _("Top X Axis Scale");
                    } else label = _("X Axis Scale");
                } else {
                    if (both_y) {
                        if (i == 3) label = _("Right Y Axis Scale");
                        else label = _("Left Y Axis Scale");
                    } else label = _("Y Axis Scale");
                }
                scales_section.append_submenu (label, scale_section);
            }
            view_menu.append_section (null, scales_section);
            view_menu_button.set_menu_model (view_menu);
        }

        public override bool close_request () {
            var application = application as Application;

            if (_force_close) {
                application.on_main_window_closed (this);
                return false;
            }

            if (data.unsaved) {
                var dialog = Tools.build_dialog ("save_project_changes") as Adw.AlertDialog;
                dialog.response.connect ((d, response) => {
                    switch (response) {
                        case "discard": {
                            _force_close = true;
                            close ();
                            break;
                        }
                        case "save": {
                            Project.save.begin (this, false, (o, result) => {
                                if (Project.save.end (result)) {
                                    _force_close = true;
                                    close ();
                                }
                            });
                            break;
                        }
                    }
                });
                dialog.present (this);
                return true;
            }
            application.on_main_window_closed (this);
            return false;
        }
    }
}
