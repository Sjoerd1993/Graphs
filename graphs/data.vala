// SPDX-License-Identifier: GPL-3.0-or-later
using Gee;

namespace Graphs {
    /**
     * Data class
     */
    public class Data : Object, Traversable<Item>, Iterable<Item> {
        protected Settings settings { get; set; }
        public FigureSettings figure_settings { get; construct set; }
        public bool can_undo { get; protected set; default = false; }
        public bool can_redo { get; protected set; default = false; }
        public bool can_view_back { get; protected set; default = false; }
        public bool can_view_forward { get; protected set; default = false; }
        public File file { get; set; }
        public bool unsaved { get; set; default = false; }
        public string project_name { get; protected set; }
        public string project_path { get; protected set; }
        public bool empty {
            get { return this._items.size == 0; }
        }
        public bool items_selected {
            get {
                foreach (Item item in this._items) {
                    if (item.selected) return true;
                }
                return false;
            }
        }

        private bool[] _used_positions;
        private Gee.AbstractList<Item> _items;

        public signal void saved ();
        protected signal void python_method_request (string method);
        protected signal void position_change_request (int index1, int index2);
        protected signal void item_changed (Item item, string prop_name);
        protected signal void delete_request (Item[] items);

        construct {
            this._items = new Gee.LinkedList<Item> ();
        }

        protected void reset () {
            this._items.clear ();
            this.file = null;
            this.unsaved = false;
        }

        public Item[] get_items () {
            return this._items.to_array ();
        }

        protected void _add_item (Item item) {
            item.notify["selected"].connect (this._on_item_selected);
            item.notify.connect (this._on_item_change);
            item.notify["xposition"].connect (this._on_item_position_change);
            item.notify["yposition"].connect (this._on_item_position_change);
            this._items.add (item);
        }

        protected void _remove_item (Item item) {
            this._items.remove (item);
        }

        public void delete_items (Item[] items) {
            this.delete_request.emit (items);
        }

        private void _on_item_selected () {
            this.notify_property ("items_selected");
        }

        private void _on_item_change (Object item, ParamSpec spec) {
            this.item_changed.emit ((Item) item, spec.name);
        }

        private void _on_item_position_change () {
            this.optimize_limits ();
            this._update_used_positions ();
            this.notify_property ("items");
        }

        public void set_items (Item[] items) {
            this._items.clear ();
            foreach (Item item in items) {
                this._add_item (item);
            }
            this._update_used_positions ();
            this.notify_property ("items");
            this.notify_property ("empty");
        }

        public string[] get_names () {
            string[] names = {};
            foreach (Item item in this._items) {
                names += item.name;
            }
            return names;
        }

        public int index (Item item) {
            return this._items.index_of (item);
        }

        public int get_n_items () {
            return this._items.size;
        }

        public Item get_at_pos (int position) {
            return this._items[position];
        }

        public Item? get_for_uuid (string uuid) {
            foreach (Item item in this._items) {
                if (item.uuid == uuid) return item;
            }
            return null;
        }

        public bool[] get_used_positions () {
            return this._used_positions;
        }

        protected void _update_used_positions () {
            if (this.empty) {
                this._used_positions = {true, false, true, false};
                return;
            }
            bool[] used_positions = {false, false, false, false};
            foreach (Item item in this._items) {
                if (this.figure_settings.hide_unselected && !item.selected)
                continue;
                used_positions[item.xposition] = true;
                used_positions[item.yposition] = true;
            }
            this._used_positions = used_positions;
        }

        public Iterator<Item> iterator () {
            return this._items.iterator ();
        }

        public bool @foreach (ForallFunc<Item> f) {
            return this._items.foreach (f);
        }

        public void optimize_limits () {
            this.python_method_request.emit ("_optimize_limits");
        }

        public void change_position (int index1, int index2) {
            this.position_change_request.emit (index1, index2);
        }

        public void add_history_state () {
            this.python_method_request.emit ("_add_history_state");
        }

        public void undo () {
            this.python_method_request.emit ("_undo");
        }

        public void redo () {
            this.python_method_request.emit ("_redo");
        }

        public void add_view_history_state () {
            this.python_method_request.emit ("_add_view_history_state");
        }

        public void view_back () {
            this.python_method_request.emit ("_view_back");
        }

        public void view_forward () {
            this.python_method_request.emit ("_view_forward");
        }
    }
}
