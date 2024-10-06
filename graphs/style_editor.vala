// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;
using Adw;

namespace Graphs {
    /**
     * Style Editor Window window
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor-window.ui")]
    public class StyleEditor : Adw.ApplicationWindow {

        [GtkChild]
        private unowned Adw.Clamp editor_clamp { get; }

        [GtkChild]
        private unowned Adw.ToolbarView content_view { get; }

        [GtkChild]
        protected unowned Adw.HeaderBar content_headerbar { get; }

        protected Gtk.Box editor_box {
            get { return editor_clamp.get_child () as Gtk.Box; }
            set { editor_clamp.set_child (value); }
        }
        protected Canvas canvas {
            get { return content_view.get_content () as Canvas; }
            set { content_view.set_content (value); }
        }

        protected CssProvider headerbar_provider { get; private set; }
        protected bool unsaved { get; set; default = false; }
        private File _file;
        private bool _force_close = false;

        protected signal void load_request (File file);
        protected signal void save_request (File file);

        construct {
            this.headerbar_provider = new CssProvider ();
            content_headerbar.get_style_context ().add_provider (
                headerbar_provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );
        }

        public void load (File file) {
            this._file = file;
            load_request.emit (file);
        }

        public void save (File file) {
            save_request.emit (file);
        }

        public override bool close_request () {
            var application = application as Application;

            if (_force_close) {
                application.on_style_editor_closed (this);
                return false;
            }

            if (unsaved) {
                var dialog = Tools.build_dialog ("save_style_changes") as Adw.AlertDialog;
                dialog.response.connect ((d, response) => {
                    switch (response) {
                        case "discard": {
                            _force_close = true;
                            close ();
                            break;
                        }
                        case "save": {
                            save_request.emit (_file);
                            _force_close = true;
                            close ();
                            break;
                        }
                    }
                });
                dialog.present (this);
                return true;
            }

            application.on_style_editor_closed (this);
            return false;
        }
    }
}
