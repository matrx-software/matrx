import json
import os
from collections import Mapping, Callable
from pathlib import Path


def get_default_value(class_name, property_name):
    defaults = load_defaults()

    if class_name in defaults:
        if property_name in defaults[class_name]:
            return defaults[class_name][property_name]
        else:
            raise Exception(f"The attribute {attribute_name} is not present in the defaults.json for class "
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


def get_all_inherited_classes(super_type):
    all_classes = {super_type}
    work = [super_type]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in all_classes:
                all_classes.add(child)
                work.append(child)

    # Create a dict out of it
    class_dict = {}
    for classes in all_classes:
        class_dict[classes.__name__] = classes

    return class_dict