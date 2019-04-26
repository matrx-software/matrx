import numpy as np
from environment.objects.helper_functions import *

class EnvObject:

    def __init__(self, obj_id, obj_name, locations, properties, is_traversable=False):
        self.obj_id = obj_id
        self.location = locations
        self.name = obj_name
        self.properties = properties
        self.is_traversable = is_traversable
        if len(np.array(self.location).shape) > 1 and np.array(self.location).shape[1] > 1:
            self.fills_multiple_locations = True
        else:
            self.fills_multiple_locations = False


    def update_properties(self, grid_world):
        """
        Used to update some properties if needed. For example a 'status' property that changes over time or due to an
        action of an agent. If you want this functionality, you should create a new object that inherits from this
        class EnvObject.
        :return: The new properties"""
        pass


    def add_properties(self, propName, propVal):
        """
        Adds a new(!) property with its value to the agent.
        """
        if propName in self.properties:
            raise Exception("Property already exists, update with update_properties instead")
        else:
            self.properties[propName] = propVal


    def get_properties(self):
        """
        Returns the properties of this object, but also its name and location(s).
        :return:
        """
        props = self.properties.copy()
        props['name'] = self.name
        props['location'] = self.location
        props['is_traversable'] = self.is_traversable
        return props

    def set_location(self, loc):
        self.location = loc
        if len(np.array(self.location).shape) > 1 and np.array(self.location).shape[1] > 1:
            self.fills_multiple_locations = True
        else:
            self.fills_multiple_locations = False


class Block(EnvObject):
    """ Block base object """

    def __init__(self, obj_id, obj_name, locations, properties):

        # set default properties of this object
        default_props = {"shape": 0, "carried": []}
        properties = set_default_properties(properties, default_props)

        # set default for customizable properties, if they are not given
        defaults_for_customizable_props = {"grootte": 1, "colour": "#0876b8", "movable": True, "size": 0.5, "is_traversable": True}
        properties = set_default_for_customizable_properties(properties, defaults_for_customizable_props)

        super().__init__(obj_id=obj_id, obj_name=obj_name, locations=locations,
                            properties=properties, is_traversable=properties["is_traversable"])


class Wall(EnvObject):
    """ Wall base object """

    def __init__(self, obj_id, obj_name, locations, properties):

        # set default properties of this object
        default_props = {"shape": 0, "size": 1, "movable": False, "carried": []}
        properties = set_default_properties(properties, default_props)

        # set default for customizable properties, if they are not given
        defaults_for_customizable_props = {"grootte": 1, "colour": "#000000"}
        properties = set_default_for_customizable_properties(properties, defaults_for_customizable_props)

        super().__init__(obj_id=obj_id, obj_name=obj_name, locations=locations,
                            properties=properties, is_traversable=False)


class Area(EnvObject):
    """ Area base object, can be used to define rooms """

    def __init__(self, obj_id, obj_name, locations, properties):
        # set default properties of this object
        default_props = {"shape": 0, "size": 1, "movable": False, "carried": []}
        properties = set_default_properties(properties, default_props)

        # set default for customizable properties, if they are not given
        defaults_for_customizable_props = {"grootte": 1, "colour": "#fbf0c3"}
        properties = set_default_for_customizable_properties(properties, defaults_for_customizable_props)

        super().__init__(obj_id=obj_id, obj_name=obj_name, locations=locations,
                            properties=properties, is_traversable=True)

class Door(EnvObject):
    """ Door base object, can be used to define rooms """

    def __init__(self, obj_id, obj_name, locations, properties):
        # set default properties of this object
        default_props = {"shape": 0, "size": 1, "movable": False, "colour": "#5a5a5a", "carried": []}
        properties = set_default_properties(properties, default_props)

        # set default for customizable properties, if they are not given
        defaults_for_customizable_props = {"grootte": 1, "door_open": False}
        properties = set_default_for_customizable_properties(properties, defaults_for_customizable_props)

        super().__init__(obj_id=obj_id, obj_name=obj_name, locations=locations,
                         properties=properties, is_traversable=properties["door_open"])
