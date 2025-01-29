// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Add Equation dialog.
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/add-equation.ui")]
    public class AddEquationDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.EntryRow equation { get; }

        [GtkChild]
        private unowned Button confirm_button { get; }

        [GtkChild]
        private unowned Adw.EntryRow item_name { get; }

        private Window window;
        private Application application;
        private GLib.Settings settings;

        public AddEquationDialog (Window window) {
            Object ();
            this.window = window;
            this.application = window.application as Application;
            this.settings = application.get_settings_child ("add-equation");
            this.equation.set_text (settings.get_string ("equation"));
            present (window);
        }

        [GtkCallback]
        private void on_accept () {
            this.settings.set_string ("equation", this.equation.get_text ());
            Item item = application.python_helper.add_equation (window, item_name.get_text ());
            Item[] items = {item};
            window.data.add_items (items);
            window.data.optimize_limits ();
            close ();
        }

        [GtkCallback]
        private void on_equation_change () {
            if (application.python_helper.validate_equation (equation.get_text ())) {
                equation.remove_css_class ("error");
                confirm_button.set_sensitive (true);
            } else {
                equation.add_css_class ("error");
                confirm_button.set_sensitive (false);
            }
        }
    }
}
