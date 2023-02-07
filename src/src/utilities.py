# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gdk
from enum import Enum

from .data import Data

def set_chooser(chooser, choice):
    """
    Set the value of a dropdown menu to the choice parameter string
    """
    model = chooser.get_model()
    for index, option in enumerate(model):
        if option.get_string() == choice:
            chooser.set_selected(index)

def empty_chooser(chooser):
    """
    Remove all the values in a dropdown menu
    """
    model = chooser.get_model()
    for item in model:
        model.remove(0)

def populate_chooser(chooser, chooser_list):
    """
    Fill the dropdown menu with the strings in a chooser_list
    """
    model = chooser.get_model()
    for item in model:
        model.remove(0)
    for item in chooser_list:
        if item != "nothing":
            model.append(str(item))
            
def get_datalist(parent):
    """
    Get a list of all data id's present in the datadict dictionary
    """
    return list(parent.datadict.keys())

def get_all_filenames(parent):
    """
    Get a list of all filenames present in the datadict dictionary
    """
    filenames = []
    for item in parent.datadict.items():
        filenames.append(item[1].filename)
    return filenames

def get_dict_by_value(dictionary, value):
    """
    Swap the keys and items of a dictionary
    """
    new_dict = dict((v, k) for k, v in dictionary.items())
    if value == "none":
        return "none"
    return new_dict[value]
    
def get_font_weight(font_name):
    """
    Get the weight of the font that is used using the full font name
    """
    valid_weights = ['normal', 'bold', 'heavy', 'light', 'ultrabold', 'ultralight']
    if font_name[-2] != "italic":
        new_weight = font_name[-2]
    else:
        new_weight = font_name[-3]
    if new_weight not in valid_weights:
        new_weight = "normal"
    return new_weight

def get_font_style(font_name):
    """
    Get the style of the font that is used using the full font name
    """
    new_style = "normal"
    if font_name[-2] == ("italic" or "oblique" or "normal"):
        new_style = font_name[-2]
    return new_style

def get_selected_keys(self):
    """
    Get a list of the ID's of all the datasets that are currently selected
    """
    selected_keys = []
    for key, item in self.item_rows.items():
        if item.check_button.get_active():
            selected_keys.append(item.id)
    return selected_keys
    
def create_data(self, xdata = [], ydata = [], name = "New data"):
    """
    Create a new dataset using the xdata, ydata and name of the dataset as argument
    """
    new_file = Data(xdata, ydata)
    new_file.filename = name
    new_file.linestyle_selected = self.preferences.config["plot_selected_linestyle"]
    new_file.linestyle_unselected = self.preferences.config["plot_unselected_linestyle"]
    new_file.selected_line_thickness = self.preferences.config["selected_linewidth"]
    new_file.unselected_line_thickness = self.preferences.config["unselected_linewidth"]
    new_file.selected_markers = self.preferences.config["plot_selected_markers"]
    new_file.unselected_markers = self.preferences.config["plot_unselected_markers"]
    new_file.selected_marker_size = self.preferences.config["plot_selected_marker_size"]
    new_file.unselected_marker_size = self.preferences.config["plot_unselected_marker_size"]
    return new_file
    
def create_rgba(r, g, b, a=1):
    """
    Create a valid RGBA object from rgba values.
    """
    res = Gdk.RGBA()
    res.red = r
    res.green = g
    res.blue = b
    res.alpha = a
    return res

class InteractionMode(Enum):
    NONE = 1
    PAN = 2
    ZOOM = 3
    SELECT = 4

