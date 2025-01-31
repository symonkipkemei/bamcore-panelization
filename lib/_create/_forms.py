from __future__ import division
# -*- coding: utf-8 -*-

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> IMPORTS

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import Transaction, Element, ElementId, FilteredElementCollector
from Autodesk.Revit.DB.Structure import StructuralType
from Autodesk.Revit.UI.Selection import ObjectType

import clr

clr.AddReference("System")

from _create import _transactions as a
from _create import _test as tt
from _create import _parts as p
from _create import _coordinate as c
from _create import _openings as o
from _create import _errorhandler as e

from pyrevit import forms
from pyrevit.forms import WPFWindow
from pyrevit import script

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> VARIABLES

app = __revit__.Application  # represents the Revit Autodesk Application
doc = __revit__.ActiveUIDocument.Document  # obj used to create new instances of elements within the active project
uidoc = __revit__.ActiveUIDocument  # obj that represent the current active project


# ________________________________________________________________________________________________


def form_display_table(data, header, table_name, last_line_color='color:red;'):
    """
    Display takeoff table
    :param data: data to be displayed
    :param header: header
    :param table_name: table name
    :param last_line_color: Last line color
    :return: None
    """
    output = script.get_output()
    output.center()
    output.add_style('body { color: blue; }')
    output.make_bar_chart(version=None)
    output.print_table(table_data=data, title=table_name, columns=header, last_line_style=last_line_color)



def form_estimated_cost():
    while True:
        cost_per_sf = forms.ask_for_string(default='0', prompt='Enter estimated cost per square feet (USD):',
                                           title='Panel Material take off')
        count = 0
        digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."]
        for ltr in cost_per_sf:
            if ltr in digits:
                count += 1
        if count == len(cost_per_sf):
            break
    return cost_per_sf


def form_displacement_distance():
    """
    User input form for selecting distance from edge of openings parameter

    :return:float option
    """
    while True:
        d_distance = forms.ask_for_string(default='0.5', prompt='Enter displacement distance from edges of openings:',
                                          title='Panelization')
        count = 0
        digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."]
        for ltr in d_distance:
            if ltr in digits:
                count += 1
        if count == len(d_distance):
            break
    return float(d_distance)


def form_select_part_type():
    """
    User input form for selecting parts for take off
    :return: String Option
    """

    # user sets cost per m2 and selects which pane to establish cost
    ops = ['External Parts', 'Internal Parts', 'External and Internal Parts']
    user_choice = forms.SelectFromList.show(ops, button_name='Select Option',
                                            title="Panel Material Takeoff", height=250)

    return user_choice


def form_switch_panelization_direction():
    '''
    User input form for switching panelization direction
    :return: Bool option
    '''
    ans = forms.ask_for_one_item(['L to R', 'R to L'], default='L to R', prompt='(L)eft to (R)ight [default]  or  (R)ight to (L)eft :',
                           title='Panelization Direction')
    if ans == "L to R":
        option = False
    elif ans == "R to L":
        option = True

    else:
        option = False

    return option

