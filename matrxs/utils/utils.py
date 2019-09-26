import json

import math
import numpy as np

from matrxs.agents.capabilities.capability import SenseCapability

object_counter = 0


def next_obj_id():
    global object_counter
    res = object_counter
    object_counter += 1
    return res


def get_inheritence_path(callable_class):
    parents = callable_class.mro()
    parents = [str(p.__name__) for p in parents]
    return parents


def get_all_classes(class_, omit_super_class=False):
    # Include given class or not
    if omit_super_class:
        subclasses = set()
    else:
        subclasses = {class_}

    # Go through all child classes
    work = [class_]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)

    # Create a dict out of it
    act_dict = {}
    for action_class in subclasses:
        act_dict[action_class.__name__] = action_class

    return act_dict


def get_all_inherited_classes(super_type):
    all_classes = {super_type}
    work = [super_type]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in all_classes:
                all_classes.add(child)
                work.append(child)

    class_dict = {}
    for classes in all_classes:
        class_dict[classes.__name__] = classes

    return class_dict


def get_distance(coord1, coord2):
    """ Get distance between two x,y coordinates """
    dist = [(a - b) ** 2 for a, b in zip(coord1, coord2)]
    dist = math.sqrt(sum(dist))
    return dist


def get_default_value(class_name, property_name):
    defaults = __load_defaults()

    if class_name in defaults:
        if property_name in defaults[class_name]:
            return defaults[class_name][property_name]
        else:
            raise Exception(f"The attribute {property_name} is not present in the defaults.json for class "
                            f"{class_name}.")
    else:
        raise Exception(f"The class name {class_name} is not present in the defaults.json.")


def __load_defaults():
    file_path = "matrxs/scenarios/defaults.json"
    return load_json(file_path)


def load_scenario(scenario_file):
    raise NotImplementedError


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

    is_steep = abs(y2 - y1) > abs(x2 - x1)
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    rev = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        rev = True

    deltax = x2 - x1
    deltay = abs(y2 - y1)
    error = int(deltax / 2)
    y = y1

    if y1 < y2:
        ystep = 1
    else:
        ystep = -1
    for x in range(x1, x2 + 1):
        if is_steep:
            line_coords.append((y, x))
        else:
            line_coords.append((x, y))
        error -= deltay
        if error < 0:
            y += ystep
            error += deltax
    # Reverse the list if the coordinates were reversed
    if rev:
        line_coords.reverse()

    return line_coords


def create_sense_capability(objects_to_perceive, range_to_perceive_them_in):
    # Check if range and objects are the same length
    assert len(objects_to_perceive) == len(range_to_perceive_them_in)

    # Check if lists are empty, if so return a capability to see all at any range
    if len(objects_to_perceive) == 0:
        return SenseCapability({"*": np.inf})

    # Create sense dictionary
    sense_dict = {}
    for idx, obj_class in enumerate(objects_to_perceive):
        perceive_range = range_to_perceive_them_in[idx]
        if perceive_range is None:
            perceive_range = np.inf
        sense_dict[obj_class] = perceive_range

    sense_capability = SenseCapability(sense_dict)

    return sense_capability
