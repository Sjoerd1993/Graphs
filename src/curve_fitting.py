# SPDX-License-Identifier: GPL-3.0-or-later
import re
from gettext import gettext as _

from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import ui, utilities
from graphs.canvas import Canvas
from graphs.data import Data
from graphs.item import DataItem

import numpy

from scipy.optimize import curve_fit


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/curve_fitting.ui")
class CurveFittingWindow(Adw.Window):
    __gtype_name__ = "GraphsCurveFittingWindow"
    equation = Gtk.Template.Child()
    fitting_params = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    text_view = Gtk.Template.Child()

    def __init__(self, application, item):
        super().__init__(
            application=application, transient_for=application.get_window(),
        )
        ui.bind_values_to_settings(
            self.get_application().get_settings("curve-fitting"), self)
        canvas = Canvas(application)
        self.param = []

        self.equation.connect("notify::text", self.on_equation_change)
        self.fitting_parameters = FittingParameterContainer(application)

        for var in self.get_free_variables():
            self.fitting_parameters.add_items([FittingParameter(name=var)])
        # Generate item for the data that is fitted to
        self.data_curve = DataItem.new(
            application, xdata=item.xdata,
            ydata=item.ydata, name=item.get_name(),
            color="#1A5FB4",
        )
        self.data_curve.linestyle = 0
        self.data_curve.markerstyle = 1
        self.data_curve.markersize = 13

        # Generate item for the fit
        self.fitted_curve = DataItem.new(
            application, xdata=[], ydata=[], color="#A51D2D",
        )

        self.fit_curve()
        self.set_entry_rows()

        canvas.props.items = [self.fitted_curve, self.data_curve]

        # Scale axis to the data to be fitted, set linear scale
        for ax in canvas.axes:
            ax.autoscale()
            ax.yscale = "linear"
            ax.xscale = "linear"
        canvas.highlight_enabled = False

        self.toast_overlay.set_child(canvas)
        self.present()

    def get_free_variables(self):
        return re.findall(
            r"\b(?!x\b|X\b|sin\b|cos\b|tan\b)[a-wy-zA-WY-Z]+\b",
            self.equation_string,
        )

    def on_equation_change(self, _entry, _param):
        for var in self.get_free_variables():
            if var not in self.fitting_parameters.get_names():
                self.fitting_parameters.add_items([FittingParameter(name=var)])
        self.fitting_parameters.remove_unused(self.get_free_variables())
        fit = self.fit_curve()
        if fit:
            self.set_entry_rows()

    def on_entry_change(self, entry, _param):
        def is_float(value):
            try:
                float(value)
                return True
            except ValueError:
                return False

        for index, row in enumerate(self.fitting_params):
            param_entries = entry

            # Get the FittingParameterEntry class corresponding to the entry
            while True:
                if isinstance(param_entries, FittingParameterEntry):
                    break
                param_entries = param_entries.get_parent()

            # Set the parameters for the row corresponding to the entry that
            # was edited
            if row == param_entries:
                initial = param_entries.initial.get_text()
                lower_bound = param_entries.lower_bound.get_text()
                upper_bound = param_entries.upper_bound.get_text()

                new_initial = (float(initial) if is_float(initial) else 1)
                new_lower_bound = (
                    lower_bound if is_float(lower_bound) else "inf")
                new_upper_bound = (
                    upper_bound if is_float(upper_bound) else "-inf")
                self.fitting_parameters[index].set_initial(new_initial)
                self.fitting_parameters[index].set_lower_bound(new_lower_bound)
                self.fitting_parameters[index].set_upper_bound(new_upper_bound)
        self.fit_curve()

    def set_results(self):
        initial_string = _("Results: \n")
        buffer_string = initial_string
        for index, arg in enumerate(self.get_free_variables()):
            buffer_string += f"\n {arg}: {self.param[index]}"

        self.text_view.get_buffer().set_text(buffer_string)
        bold_tag = Gtk.TextTag(weight=700)
        self.text_view.get_buffer().get_tag_table().add(bold_tag)

        start_iter = self.text_view.get_buffer().get_start_iter()
        end_iter = self.text_view.get_buffer().get_start_iter()

        # Highlight first word
        while not end_iter.ends_word() and not end_iter.ends_sentence():
            end_iter.forward_char()
        self.text_view.get_buffer().apply_tag(bold_tag, start_iter, end_iter)

    @property
    def equation_string(self):
        return utilities.preprocess(str(self.equation.get_text()))

    def fit_curve(self):
        def _get_equation_name(equation_name, values):
            var_to_val = dict(zip(self.get_free_variables(), values))

            for var, val in var_to_val.items():
                equation_name = equation_name.replace(var, str(round(val, 3)))
            return equation_name

        function = utilities.string_to_function(self.equation_string)
        if function is None:
            return
        try:
            self.param, param_cov = curve_fit(
                function,
                self.data_curve.xdata, self.data_curve.ydata,
                p0=self.fitting_parameters.get_p0(),
                bounds=self.fitting_parameters.get_bounds(), nan_policy="omit",
            )
        except (ValueError, TypeError):
            # Cancel fit if not succesfull
            return
        xdata = numpy.linspace(
            min(self.data_curve.xdata), max(self.data_curve.xdata), 5000,
        )
        ydata = [function(x, *self.param) for x in xdata]

        name = _get_equation_name(
            str(self.equation.get_text()), self.param)
        self.fitted_curve.set_name(f"Y = {name}")
        self.fitted_curve.ydata, self.fitted_curve.xdata = (ydata, xdata)
        self.set_results()
        return True

    @Gtk.Template.Callback()
    def add_fit(self, _widget):
        """Add fitted data to the items in the main application"""
        self.get_application().get_data().add_items([DataItem.new(
            self.get_application(), name=self.fitted_curve.get_name(),
            xdata=self.fitted_curve.xdata, ydata=self.fitted_curve.ydata,
        )])
        self.destroy()

    def set_entry_rows(self):
        while self.fitting_params.get_last_child() is not None:
            self.fitting_params.remove(self.fitting_params.get_last_child())

        for arg in self.get_free_variables():
            self.fitting_params.append(FittingParameterEntry(self, arg))


class FittingParameterContainer(Data):
    """Class to contain the fitting parameters."""
    __gtype_name__ = "GraphsFittingParameterContainer"
    __gsignals__ = {}

    def add_items(self, items):
        for item in items:
            self._items[item.get_name()] = item

    def remove_unused(self, used_list):
        # First create list with items to remove
        # to avoid dict changing size during iteration
        remove_list = []
        for item in self._items.values():
            if item.get_name() not in used_list:
                remove_list.append(item.get_name())

        for item_name in remove_list:
            del self._items[item_name]

        self.order_by_list(used_list)

    def order_by_list(self, ordered_list):
        self._items = {key: self._items[key] for key in ordered_list}

    def get_p0(self) -> list:
        """Get the initial values."""
        return [float(item_.get_initial()) for item_ in self]

    def get_bounds(self):
        lower_bounds = [float(item_.get_lower_bound()) for item_ in self]
        upper_bounds = [float(item_.get_upper_bound()) for item_ in self]
        return (lower_bounds, upper_bounds)


class FittingParameter(Graphs.FittingParameter):
    """Class for the fitting parameters."""
    __gtype_name__ = "GraphsFittingParameterItem"
    application = GObject.Property(type=object)

    def __init__(self, **kwargs):
        super().__init__(name=kwargs.get("name", ""),
                         initial=kwargs.get("initial", 1),
                         lower_bound=kwargs.get("lower_bound", "-inf"),
                         upper_bound=kwargs.get("upper_bound", "inf"),
                         )


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/fitting_parameters.ui")
class FittingParameterEntry(Gtk.Box):
    __gtype_name__ = "GraphsFittingParameterEntry"
    label = Gtk.Template.Child()
    initial = Gtk.Template.Child()
    upper_bound = Gtk.Template.Child()
    lower_bound = Gtk.Template.Child()

    application = GObject.Property(type=Adw.Application)

    def __init__(self, parent, arg):
        super().__init__(application=parent.get_application())
        self.parent = parent
        self.params = parent.fitting_parameters[arg]
        self.label.set_markup(
            f"<b>Fitting parameters for {self.params.get_name()}: </b>")
        self.initial.set_text(str(self.params.get_initial()))

        self.initial.connect("notify::text", parent.on_entry_change)
        self.upper_bound.connect("notify::text", parent.on_entry_change)
        self.lower_bound.connect("notify::text", parent.on_entry_change)
