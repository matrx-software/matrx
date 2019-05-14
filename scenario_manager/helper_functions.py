import json
import os
from collections import Mapping, Callable
from pathlib import Path

from shapely.geometry import Polygon, Point


def get_default_value(class_name, property_name):
    defaults = load_defaults()

    if class_name in defaults:
        if property_name in defaults[class_name]:
            return defaults[class_name][property_name]
        else:
            raise Exception(f"The attribute {property_name} is not present in the defaults.json for class "
                            f"{class_name}.")
    else:
        raise Exception(f"The class name {class_name} is not present in the defaults.json.")


def load_defaults():
    # Find the testbed's root path (searches through all the file's parents until the folder testbed is reached)
    root_path = None
    for parent in reversed(list(Path(__file__).parents)):
        if "testbed" in str(parent):
            root_path = parent
            break

    file_path = os.path.join(root_path, "scenarios", "defaults.json")
    return load_json(file_path)


def load_scenario(scenario_file):
    scenario_file = scenario_file

    # Find the testbed's root path (searches through all the file's parents until the folder testbed is reached)
    root_path = None
    for parent in reversed(list(Path(__file__).parents)):
        if "testbed" in str(parent):
            root_path = parent
            break

    scenario_path = os.path.join(root_path, "scenarios", scenario_file)
    return load_json(scenario_path)


def load_json(file_path):
    with open(file_path, "r") as read_file:
        json_dict = json.load(read_file)
    return json_dict


def _get_line_coords(p1, p2):

    line_coords = []

    x1 = int(p1[0])
    x2 = int(p2[0])
    y1 = int(p1[1])
    y2 = int(p2[1])
    xdiff = x2 - x1
    ydiff = y2 - y1

    # Find the line's equation, y = mx + b
    strt = x1 + 1
    nd = x2
    if xdiff != 0 and ydiff != 0:
        m = ydiff / xdiff
        b = y1 - m * x1
    elif ydiff == 0:
        m = 0
        b = y2
        strt = x1
        nd = x2
    elif xdiff == 0:
        m = 0
        b = x2
        strt = y1
        nd = y2

    temp_strt = min(strt, nd)
    nd = max(nd, strt)
    strt = temp_strt + 1
    for val in range(strt, nd):
        res = int(m * val + b)
        if int(res) == res:
            if xdiff == 0:
                line_coords.append((res, val))
            else:
                line_coords.append((val, res))

    return line_coords


def _get_hull_and_volume_coords(corner_coords):
        # Check if there are any corners given
        if len(corner_coords) <= 1:
            raise Exception("Cannot create area; No or just one corner coordinate given.")

        # Get the polygon represented by the corner coordinates
        # TODO remove the dependency to Shapely
        polygon = Polygon(corner_coords)

        (minx, miny, maxx, maxy) = polygon.bounds
        minx = int(minx)
        miny = int(miny)
        maxx = int(maxx)
        maxy = int(maxy)

        volume_coords = []
        for x in range(minx, maxx + 1):
            for y in range(miny, maxy + 1):
                p = Point(x, y)
                if polygon.contains(p):
                    volume_coords.append((x, y))

        hull_coords = []
        corners = list(zip(polygon.exterior.xy[0], polygon.exterior.xy[1]))
        for idx in range(len(corners) - 1):
            p1 = corners[idx]
            p2 = corners[idx + 1]
            line_coords = _get_line_coords(p1, p2)
            hull_coords.extend(line_coords)

        # Add corners as well
        for corner in corner_coords:
            hull_coords.append(tuple(corner))

        return hull_coords, volume_coords