from __future__ import division
# -*- coding: utf-8 -*-

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> IMPORTS

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import Transaction, Element, ElementId, FilteredElementCollector
from Autodesk.Revit.DB.Structure import StructuralType
from Autodesk.Revit.UI.Selection import ObjectType

import clr

clr.AddReference("System")

from _create import _auto as a

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> VARIABLES

app = __revit__.Application  # represents the Revit Autodesk Application
doc = __revit__.ActiveUIDocument.Document  # obj used to create new instances of elements within the active project
uidoc = __revit__.ActiveUIDocument  # obj that represent the current active project

# create
active_view = doc.ActiveView
active_level = doc.ActiveView.GenLevel


def get_host_wall_id(part):
    """
    Retrieves the host wall id, when a Part is selected
    :param part: selected part
    :return: host_wall_id
    """
    linkedElementIdCollection = part.GetSourceElementIds()
    host_wall_id = linkedElementIdCollection[0].HostElementId  # pick first linkedelement in collection

    return host_wall_id


def get_host_wall_type_id(host_wall_id):
    """
    Abstract the type of the wall
    :param host_wall_id: id of the wall
    :return: id of the wall type
    """
    host_wall = doc.GetElement(host_wall_id)
    type_id = host_wall.GetTypeId()

    return type_id


def select_all_parts():
    """Selects all parts in a project"""
    all_parts = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Parts). \
        WhereElementIsNotElementType().ToElements()

    return all_parts


def select_part():
    """Selects a part from the uidoc
    :return: returns the Part object
    """
    # select part element
    reference = uidoc.Selection.PickObject(ObjectType.Element)
    part = uidoc.Document.GetElement(reference)

    if str(type(part)) == "<type 'Part'>":
        return part
    else:
        print("Select a Part for it to be multi-panelized, you've selected", type(part))



def get_edge_index(__title__, part, host_wall_id, lap_type_id, variable_distance, side_of_wall):
    """
    Get the edge indexes ( left and right) when a part is selected
    :param __title__: tool title
    :param part: selected part
    :param variable_distance: distance from reveal at 0
    :param side_of_wall: side to place reveals
    :return:
    """


    global left_edge_index, right_edge_index

    # abstract the length of the part
    part_length = part.get_Parameter(BuiltInParameter.DPART_LENGTH_COMPUTED).AsDouble()
    print("PART_LENGTH", part_length)

    # split parts  by placing a reveal: old_part(retains the original part Id), new_part (assigned a new part id)

    with Transaction(doc, __title__) as t:
        t.Start()
        fst_wall_sweep = a.auto_reveal(host_wall_id, lap_type_id, variable_distance, side_of_wall)
        t.Commit()

    # get old_part_length
    old_part_length_before_snd_reveal = part.get_Parameter(BuiltInParameter.DPART_LENGTH_COMPUTED).AsDouble()

    # create snd wall sweep
    move_distance = 0.166667  # 1/4", small distance to ensure part is cut
    with Transaction(doc, __title__) as t:
        t.Start()
        snd_wall_sweep = a.auto_reveal(host_wall_id, lap_type_id, (variable_distance + move_distance), side_of_wall)
        t.Commit()

    # get old_part_length after snd reveal
    old_part_length_after_snd_reveal = part.get_Parameter(BuiltInParameter.DPART_LENGTH_COMPUTED).AsDouble()

    print("OLD PART LENGTH BEFORE SND REVEAL", old_part_length_before_snd_reveal)
    print("OLD PART LENGTH AFTER SND REVEAL", old_part_length_after_snd_reveal)

    # determine the edge index in reference to reveal at 0
    if old_part_length_after_snd_reveal == old_part_length_before_snd_reveal and old_part_length_after_snd_reveal != part_length:  # the old part is on the right, not
        # affected by reveal moving (moves right to left)
        left_edge_index = (part_length - (old_part_length_before_snd_reveal- variable_distance))
        right_edge_index = left_edge_index - part_length

    elif old_part_length_after_snd_reveal != old_part_length_before_snd_reveal:  # the old part is on the left
        # affected by reveal moving (moves right to left)
        # delete second reveal

        left_edge_index = old_part_length_before_snd_reveal - variable_distance
        right_edge_index = left_edge_index - part_length

    elif old_part_length_after_snd_reveal == part_length:
        print ("The walls are non-orthogonal, \nthe reveals did not cut through the part \nRepeat this manually")

    else:
        print ("Raise an error")
        print ("The move tool is dysfunctional, check for errors")

    # delete reveals after abstracting the edge indexes
    with Transaction(doc, __title__) as t:
        t.Start()

        doc.Delete(fst_wall_sweep.Id)
        doc.Delete(snd_wall_sweep.Id)

        t.Commit()

    return left_edge_index, right_edge_index



def get_reveal_indexes(left_edge, right_edge, exterior_face=True):
    """
    Retrieve the posiyion to place reveals
    :param left_edge: The left edge of the wall ( from exterior)
    :param right_edge: The right edge of the wall ( from exterior)
    :param panel_size: The size of each panel
    :param exterior_face: if exterior face, the panel position starts from left to right
    and right to left if not exterior face
    :return: the indexes of the reveal position
    """

    # place reveal at correct position
    part_length = left_edge - right_edge
    panel_size = 3.927083  # 3' 11 1/8"
    half_panel_size = 1.927083  # 1' 11 1/8"
    minimum_panel = 2
    reveal_width = 0.072917  # the width of the reveal 7/8"

    no_complete_panels = int(part_length // panel_size)
    incomplete_panel_length = part_length % panel_size

    # store all reveal indexes
    reveal_indexes = []

    if incomplete_panel_length == 0:  # the length of Parts can be divided perfectly into panels
        if exterior_face:
            for x in range(0, no_complete_panels):
                left_edge -= panel_size
                reveal_indexes.append(left_edge)
        else:
            right_edge = right_edge + reveal_width
            for x in range(0, no_complete_panels):
                right_edge += panel_size
                reveal_indexes.append(right_edge)


    elif incomplete_panel_length < 2:  # the remaining length after whole panels, if less than 2', split previous panel,
        # the remainder would be less than 4'
        if exterior_face:
            for x in range(0, (no_complete_panels - 1)):
                left_edge -= panel_size
                reveal_indexes.append(left_edge)
            left_edge -= half_panel_size
            reveal_indexes.append(left_edge)

        else:
            right_edge = right_edge + reveal_width  # to allow reveals cut internal panels at 4'
            for x in range(0, (no_complete_panels - 1)):
                right_edge += panel_size
                reveal_indexes.append(right_edge)
            right_edge += half_panel_size
            reveal_indexes.append(right_edge)

    elif incomplete_panel_length > minimum_panel:  # the remaining length after whole panels, if greater than 2', retain it
        if exterior_face:
            for x in range(0, no_complete_panels):
                left_edge -= panel_size
                reveal_indexes.append(left_edge)
        else:
            right_edge = right_edge + reveal_width
            for x in range(0, no_complete_panels):
                right_edge += panel_size
                reveal_indexes.append(right_edge)

    else:
        print ("The incomplete panel length is unknown or faulty")

    # check if there is a remainder
    return reveal_indexes


def get_single_panel_reveal_indexes(left_edge, right_edge, exterior_face=True):
    """Determine the position of a reveal index for a single panel
    :param left_edge:
    :param right_edge:
    :param exterior_face:
    :return:
    """
    panel_size = 3.927083
    reveal_indexes = []
    if exterior_face:
        new_reveal_distance = left_edge - panel_size
        reveal_indexes.append(new_reveal_distance)

    else:
        new_reveal_distance = right_edge + panel_size
        reveal_indexes.append(new_reveal_distance)

    return reveal_indexes


def get_layer_index(part):
    """
    Abstract the layer index of a part if
    layer Index 1- Exterior face
    layer Index 2 - internal partition walls
    layer Index 3- Interior face

    :param part: Part to be abstracted
    :return: The layer index
    """
    # abstract the layer index of part
    layer_index = int(part.get_Parameter(BuiltInParameter.DPART_LAYER_INDEX).AsString())
    return layer_index


def check_if_parts_panelized(parts):
    """
    Filter parts that have not been panelized only, to avoid panelizing panels further
    :param parts: list of parts selected from an open revit document
    :return: filter list of parts yet to be panelized
    """
    parts_to_panelize = []
    for part in parts:
        part_length = part.get_Parameter(BuiltInParameter.DPART_LENGTH_COMPUTED).AsDouble()
        if part_length > 4:
            parts_to_panelize.append(part)

    return parts_to_panelize


def move_wall_sweep(__title__, x_axis, left_right, wall_sweep, move_distance):
    """
    Move sweep by a particular distance depending on the wall orientation
    :param left_right: The direction of move
    :param x_axis: if wall is on x or y plane
    :param __title__: Tool title
    :param move_distance: The distance to move by
    :param wall_sweep: The sweep to be moved

    """

    print ("X axis", x_axis)
    print ("left_right", left_right)

    with Transaction(doc, __title__) as t:
        t.Start()

        if x_axis:
            if left_right:
                location = wall_sweep.Location.Move(XYZ(move_distance, 0, 0))
            elif not left_right:
                location = wall_sweep.Location.Move(XYZ((0 - move_distance), 0, 0))

        elif not x_axis:
            if left_right:
                location = wall_sweep.Location.Move(XYZ(0, (0 - move_distance), 0))
            elif not left_right:
                location = wall_sweep.Location.Move(XYZ(0, move_distance, 0))

        t.Commit()


def get_wall_orientation(host_wall_id):
    """
    Determines the orientation of the wall
    :param host_wall_id: The selected wall
    :return: The orientation of the wall
    """

    global x_axis, left_right

    # abstract orientation data from revit
    host_wall = doc.GetElement(host_wall_id)
    orientation = host_wall.Orientation

    # determine if the wall is x or y-axis plane
    if orientation[0] == -1 or orientation[0] == 1:  # Y Axis
        # determine direction of move
        x_axis = False
        if orientation[0] == 1:  # moves left to right
            left_right = False
        elif orientation[0] == -1:  # moves right to left
            left_right = True

    elif orientation[1] == -1 or orientation[1] == 1:  # X axis
        x_axis = True
        if orientation[1] == 1:  # moves left to right
            left_right = True
        elif orientation[1] == -1:  # moves right to left
            left_right = False

    else:
        print ("The wall is not orthogonal and does not belong to a particular plane")

    return x_axis, left_right


