import numpy as np


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
            print("Property already exists, update with update_properties instead")
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

    def set_location(self, locs):
        self.location = locs
        if len(np.array(self.location).shape) > 1 and np.array(self.location).shape[1] > 1:
            self.fills_multiple_locations = True
        else:
            self.fills_multiple_locations = False


class AgentAvatar(EnvObject):

    def __init__(self, agent_id, agent_name, location, sense_capability, action_set, get_action_func,
                 set_action_result_func, properties):
        super().__init__(obj_id=agent_id, obj_name=agent_name, locations=location, properties=properties)
        self.sense_capability = sense_capability
        self.action_set = action_set
        self.get_action_func = get_action_func
        self.set_action_result_func = set_action_result_func
