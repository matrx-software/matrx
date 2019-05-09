import numpy as np
from environment.objects.helper_functions import *


class EnvObject:

    def __init__(self, obj_id, obj_name, location, properties, is_traversable):
        self.obj_id = obj_id
        self.name = obj_name
        self.properties = properties

        # These are mandatory things the grid world expect each EnvObject to have
        self.is_traversable = is_traversable  # whether agents can traverse over this object
        self.carried_by = []  # a list of agent ids that denote who is carrying this object (if any)
        self.vis_size = 1  # the size for the visualisation
        self.vis_shape = 0  # the shape for the visualisation
        self.vis_colour = "#000000"  # the colour for the visualisation

        # location should be set at the end (due to the dependency of its setter on the other attributes (e.g. in
        # AgentAvatar)
        self.location = location

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

    @property
    def location(self):
        """
        The location of any object is a pythonic property, this allows us to do various checks on it. One of them is the
        setter that is overridden in AgentAvatar to also transfer all carried objects with it.
        :return: The current location as a tuple; (x, y)
        """
        return tuple(self.__location)

    @location.setter
    def location(self, loc):
        """
        The setter than can be overridden if a location change might also affect some other things inside the
        AgentAvatar.
        :param loc: The new location
        :return: None
        """
        self.__location = loc


class Block(EnvObject):
    """ Block base object """

    def __init__(self, obj_id, obj_name, location, properties, is_traversable=True):
        # set default properties of this object
        default_props = {"shape": 0, "carried": []}
        properties = set_default_properties(properties, default_props)

        # set default for customizable properties, if they are not given
        defaults_for_customizable_props = {"colour": "#0876b8", "movable": True, "size": 0.5, "is_traversable": True}
        properties = set_default_for_customizable_properties(properties, defaults_for_customizable_props)

        super().__init__(obj_id=obj_id, obj_name=obj_name, location=location,
                         properties=properties, is_traversable=is_traversable)


class Wall(EnvObject):
    """ Wall base object """

    def __init__(self, obj_id, obj_name, location, properties, is_traversable=False):
        # set default properties of this object
        default_props = {"shape": 0, "size": 1, "movable": False, "carried_by": []}
        properties = set_default_properties(properties, default_props)

        # set default for customizable properties, if they are not given
        defaults_for_customizable_props = {"colour": "#000000"}
        properties = set_default_for_customizable_properties(properties, defaults_for_customizable_props)

        super().__init__(obj_id=obj_id, obj_name=obj_name, location=location,
                         properties=properties, is_traversable=is_traversable)


class Area(EnvObject):
    """ Area base object, can be used to define rooms """

    def __init__(self, obj_id, obj_name, location, properties, is_traversable=True):
        # set default properties of this object
        default_props = {"shape": 0, "size": 1, "movable": False, "carried_by": []}
        properties = set_default_properties(properties, default_props)

        # set default for customizable properties, if they are not given
        defaults_for_customizable_props = {"colour": "#fbf0c3"}
        properties = set_default_for_customizable_properties(properties, defaults_for_customizable_props)

        super().__init__(obj_id=obj_id, obj_name=obj_name, location=location,
                         properties=properties, is_traversable=is_traversable)


class Door(EnvObject):
    """ Door base object, can be used to define rooms """

    def __init__(self, obj_id, obj_name, location, properties, is_traversable=False):
        # set default properties of this object
        default_props = {"shape": 0, "size": 1, "movable": False, "colour": "#5a5a5a", "carried_by": []}
        properties = set_default_properties(properties, default_props)

        # set default for customizable properties, if they are not given
        defaults_for_customizable_props = {"grootte": 1, "door_open": is_traversable}
        properties = set_default_for_customizable_properties(properties, defaults_for_customizable_props)

        super().__init__(obj_id=obj_id, obj_name=obj_name, location=location,
                         properties=properties, is_traversable=properties["door_open"])
