from __future__ import division

# METADATA

__title__ = "Test"

__doc__ = """Version  1.0
Date  = 09.07.2023
___________________________________________________________
Description:

Devlopment environment for testing bugs and features before development

___________________________________________________________
How-to:
-> Click on the button
___________________________________________________________
last update:
- [09.07.2023] - 1.0 RELEASE

___________________________________________________________
To do:
-> Testing and development
___________________________________________________________
Author: Symon Kipkemei

"""

__author__ = "Symon Kipkemei"
__helpurl__ = "https://www.linkedin.com/in/symon-kipkemei/"

__highlight__ = 'new'

__min_revit_ver__ = 2020
__max_revit_ver__ = 2023

# IMPORTS
################################################################################################################################

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import Transaction, Element, ElementId, FilteredElementCollector
from Autodesk.Revit.DB.Structure import StructuralType
from Autodesk.Revit.UI.Selection import ObjectType
import clr

clr.AddReference("System")

from _create import _auto as a
from _create import _get as g

# VARIABLES
################################################################################################################################

# __revit__  used to create an instance
app = __revit__.Application  # represents the Revit Autodesk Application
doc = __revit__.ActiveUIDocument.Document  # obj used to create new instances of elements within the active project
uidoc = __revit__.ActiveUIDocument  # obj that represent the current active project

# create
active_view = doc.ActiveView
active_level = doc.ActiveView.GenLevel


def get_edge_index(__title__, part, host_wall_id, lap_type_id, variable_distance, side_of_wall):
    """
    Get the edge indexes ( left and right) when a part is selected
    :param __title__: tool title
    :param part: selected part
    :param variable_distance: distance from reveal at 0
    :param side_of_wall: side to place reveals
    :return:
    """

    # abstract the length of the part
    part_length = part.get_Parameter(BuiltInParameter.DPART_LENGTH_COMPUTED).AsDouble()
    print("PART_LENGTH", part_length)

    # split parts  by placing a reveal: old_part(retains the original part Id), new_part (assigned a new part id)

    with Transaction(doc, __title__) as t:
        t.Start()
        wall_sweep = a.auto_reveal(host_wall_id, lap_type_id, variable_distance, side_of_wall)
        t.Commit()

    # get old_part_length
    old_part_length_before_move = part.get_Parameter(BuiltInParameter.DPART_LENGTH_COMPUTED).AsDouble()

    new_part_length = part_length - old_part_length_before_move

    # move sweep, to determine the placement/orientation of the two parts
    move_distance = 0.010417  # 1/8", small distance to ensure part is cut
    x_axis, left_right = get_wall_orientation(host_wall_id)
    move_wall_sweep(__title__, x_axis, left_right, wall_sweep, move_distance)

    # get old length (after moving wall sweep)
    old_part_length_after_move = part.get_Parameter(BuiltInParameter.DPART_LENGTH_COMPUTED).AsDouble()

    print("OLD PART LENGTH BEFORE MOVE", old_part_length_before_move)
    print("OLD PART LENGTH AFTER MOVE", old_part_length_after_move)
    print("NEW PART LENGTH", new_part_length)

    # determine the edge index in reference to reveal at 0
    if old_part_length_after_move > old_part_length_before_move:  # the old part is on the right
        left_edge_index = part_length - old_part_length_before_move
        right_edge_index = left_edge_index - part_length

    elif old_part_length_after_move < old_part_length_before_move:  # the old part is on the right
        left_edge_index = old_part_length_before_move
        right_edge_index = left_edge_index - part_length

    elif old_part_length_after_move == old_part_length_before_move:
        print ("Raise an error")
        print ("The move tool is dysfunctional, check for errors")

    # delete reveal after abstracting the edge indexes
    with Transaction(doc, __title__) as t:
        t.Start()
        doc.Delete(wall_sweep.Id)
        t.Commit()

    return left_edge_index, right_edge_index


def move_wall_sweep(__title__, x_axis, left_right, wall_sweep, move_distance):
    """
    Move sweep by a particular distance,
    to check if panel if it's on right or left
    :param host_wall_id: To determine wall orientation
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
    :return: If wall is negative or positive
    """

    global x_axis, left_right

    # abstract orientation data from revit
    host_wall = doc.GetElement(host_wall_id)
    orientation = host_wall.Orientation

    # determine if the wall is x or y-axis plane
    if orientation[0] == -1 or orientation[0] == 1: # Y Axis
        # determine direction of move
        x_axis = False
        if orientation[0] == 1: # moves left to right
            left_right = False
        elif orientation[0] == -1: # moves right to left
            left_right = True

    elif orientation[1] == -1 or orientation[1] == 1:  # X axis
        x_axis = True
        if orientation[1] == 1: # moves left to right
            left_right = True
        elif orientation[1] == -1: # moves right to left
            left_right = False

    else:
        print ("The wall is not orthogonal and does not belong to a particular plane")

    return x_axis, left_right


def test():
    part = g.select_part()
    host_wall_id = g.get_host_wall_id(part)
    side_of_wall = WallSide.Exterior
    lap_type_id = ElementId(352808)
    variable_distance = 0
    left_edge, right_edge = get_edge_index(__title__, part, host_wall_id, lap_type_id, variable_distance,
                                           side_of_wall)
    panel_size = 3.927083

    # place reveals at left edge ,0 and  right edge
    a.auto_place_reveal(__title__, host_wall_id, lap_type_id, (left_edge - panel_size), side_of_wall)
    # a.auto_place_reveal(__title__, host_wall_id, lap_type_id, variable_distance, side_of_wall)
    # a.auto_place_reveal(__title__, host_wall_id, lap_type_id, (right_edge + panel_size), side_of_wall)

    print (left_edge, right_edge)


def main(host_wall_id):
    # select a part
    reference = uidoc.Selection.PickObject(ObjectType.Element)
    wall_sweep = uidoc.Document.GetElement(reference)
    distance = 6
    x_axis_bool, left_right_bool = get_wall_orientation(host_wall_id)
    move_wall_sweep(__title__, x_axis_bool, left_right_bool, wall_sweep, distance)


if __name__ == "__main__":
    #main(ElementId(713033)) #short side
    main(ElementId(713030)) #longside A
    #main(ElementId(713032)) #longside B --
    #test()

