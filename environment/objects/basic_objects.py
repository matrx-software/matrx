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



class AgentAvatar(EnvObject):
    """
    This class is a representation of an agent in the GridWorld.
    It is used as a measure to keep the real Agent code and Environment code
    seperate. This AgentAvatar is used by the environment to update the GUI, perform actions,
    and update properties. It is kept in sync with the real Agent object every iteration.
    """

    def __init__(self, agent_id, sense_capability, action_set, get_action_func,
                 set_action_result_func, agent_properties, properties_agent_writable, type):

        # define which properties are required for the agent
        self.required_props = ["location", "size", "is_traversable", "colour", "shape", "name"]

        # check validity of the passed properties
        self.__check_properties_validity(agent_id, agent_properties)

        # create an Env obj from this agent
        super().__init__(   obj_id=agent_id,
                            obj_name=agent_properties["name"],
                            locations=agent_properties["location"],
                            properties=agent_properties,
                            is_traversable=agent_properties["is_traversable"])

        # save the other
        self.sense_capability = sense_capability
        self.action_set = action_set
        self.get_action_func = get_action_func
        self.set_action_result_func = set_action_result_func
        self.type = type
        self.properties_agent_writable = properties_agent_writable


    def __check_properties_validity(self, id, props):
        """
        Check if all required properties are present
        :param id {int}:        (human)agent_id
        :param props {dict}:    dictionary with agent properties
        """
        # check if all required properties have been defined
        for prop in self.required_props:
            if prop not in props:
                raise Exception(f"The (human) agent with {id} is missing the property {prop}. \
                        All of the following required properties need to be defined: {self.required_props}.")



    def set_agent_changed_properties(self, props):
        """
        The Agent has possibly changed some of its properties during its OODA loop.
        Here the agent properties are also updated in the Agent Avatar, if it
        was not a agent_read_only property.
        """
        # get all agent properties of this Agent Avatar in one dictionary
        AA_props = self.get_properties()

        # check for each property if it has been changed by the agent, and if we need
        # to update our local copy (here in Agent Avatar) of the agent properties to match that
        for prop in props:
            if prop not in AA_props:
                raise Exception(f"Agent {self.obj_id} tried to remove the property {prop}, which is not allowed.")

            # check if the property has changed, and skip if not the case
            if props[prop] == AA_props[prop]:
                continue

            # if the agent has changed the property, check if the agent has permission to do so
            if prop not in self.properties_agent_writable:
                raise Exception(f"Agent {self.obj_id} tried to change a non-writable property: {prop}.")

            ## the agent changed the property and the agent had permission to do so
            # update special properties
            if prop == 'location':
                self.location = props[prop]
            elif prop == "is_traversable":
                self.is_traversable = props[prop]
            elif prop == "name":
                self.name = props[prop]
            # update normal properties
            else:
                self.properties = props[prop]
