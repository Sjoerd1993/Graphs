// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;

namespace Graphs {
    public class Application : Adw.Application {
        public Window window { get; set; }
        public Settings settings { get; construct set; }
        public FigureSettings figure_settings { get; construct set; }
        public DataInterface data { get; construct set; }
        public ClipboardInterface clipboard { get; construct set; }
        public ClipboardInterface view_clipboard { get; construct set; }
        public int mode { get; set; default = 0; }

        public string version { get; construct set; default = ""; }
        public string name { get; construct set; default = ""; }
        public string website { get; construct set; default = ""; }
        public string issues { get; construct set; default = ""; }
        public string author { get; construct set; default = ""; }
        public string pkgdatadir { get; construct set; default = ""; }
    }
}
