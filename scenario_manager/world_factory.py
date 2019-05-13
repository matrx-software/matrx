import numpy as np

from agents.Agent import Agent
from agents.capabilities.capability import SenseCapability
from environment.objects.env_object import EnvObject


class WorldFactory:

    def __init__(self, random_seed=1):
        self.rng = np.random.RandomState(random_seed)
        self.agent_settings = []
        self.object_settings = []
        self.worlds_created = 0

    def add_agent(self, location, agent, custom_properties=None, sense_capability=None, customizable_properties=None,
                  is_traversable=None, team=None, agent_speed_in_ticks=None, visualize_size=None, visualize_shape=None,
                  visualize_colour=None):

        # Check if location and agent are of correct type
        assert isinstance(location, list) or isinstance(location, tuple)
        assert isinstance(agent, Agent)

        # If default variables are not given, assign them (most empty, except of sense_capability that defaults to all
        # objects with infinite range).
        if custom_properties is None:
            custom_properties = []
        if sense_capability is None:
            sense_capability = self.create_sense_capability([], [])
        if customizable_properties is None:
            customizable_properties = []

        agent_setting = {"agent": agent,
                         "custom_properties": custom_properties,
                         "customizable_properties": customizable_properties,
                         "sense_capability": sense_capability,
                         "mandatory_properties": {
                             "name": agent.agent_name,
                             "is_traversable": is_traversable,
                             "agent_speed_in_ticks": agent_speed_in_ticks,
                             "visualize_size": visualize_size,
                             "visualize_shape": visualize_shape,
                             "visualize_colour": visualize_colour,
                             "location": location,
                             "team": team}
                         }

        self.agent_settings.append(agent_setting)

    def add_team(self, agents, locations, team_name, custom_properties=None, sense_capability=None,
                 customizable_properties=None, is_traversable=None, agent_speed_in_ticks=None,
                 visualize_size=None, visualize_shape=None, visualize_colour=None):

        self.add_multiple_agents(agents, locations, custom_properties=custom_properties,
                                 sense_capabilities=sense_capability, customizable_properties=customizable_properties,
                                 is_traversable=is_traversable, agent_speeds_in_ticks=agent_speed_in_ticks,
                                 teams=team_name, visualize_sizes=visualize_size, visualize_shapes=visualize_shape,
                                 visualize_colours=visualize_colour)

    def add_multiple_agents(self, agents, locations, custom_properties=None,
                            sense_capabilities=None, customizable_properties=None,
                            is_traversable=None, agent_speeds_in_ticks=None,
                            teams=None, visualize_sizes=None, visualize_shapes=None,
                            visualize_colours=None):

        if custom_properties is None:
            custom_properties = [None for _ in range(len(agents))]
        if sense_capabilities is None:
            sense_capabilities = [None for _ in range(len(agents))]
        if customizable_properties is None:
            customizable_properties = [None for _ in range(len(agents))]
        if is_traversable is None:
            is_traversable = [None for _ in range(len(agents))]
        if agent_speeds_in_ticks is None:
            agent_speeds_in_ticks = [None for _ in range(len(agents))]
        if teams is None:
            teams = [None for _ in range(len(agents))]
        if visualize_sizes is None:
            visualize_sizes = [None for _ in range(len(agents))]
        if visualize_shapes is None:
            visualize_shapes = [None for _ in range(len(agents))]
        if visualize_colours is None:
            visualize_colours = [None for _ in range(len(agents))]

        for idx, agent in enumerate(agents):
            location = locations[idx]

            self.add_agent(location, agent,
                           custom_properties=custom_properties[idx],
                           sense_capability=sense_capabilities[idx],
                           customizable_properties=customizable_properties[idx],
                           is_traversable=is_traversable[idx],
                           team=teams[idx],
                           agent_speed_in_ticks=agent_speeds_in_ticks[idx],
                           visualize_size=visualize_sizes[idx],
                           visualize_shape=visualize_shapes[idx],
                           visualize_colour=visualize_colours[idx])

    def add_env_object(self, location, env_object):

        # Check if location and env_object are of correct type
        assert isinstance(location, list) or isinstance(location, tuple)
        assert isinstance(env_object, EnvObject)

        self.object_settings.append({"env_object": env_object})

    def add_multiple_objects(self):
        pass

    def add_area(self):
        pass

    def create_sense_capability(self, objects_to_perceive, range_to_perceive_them_in):
        # Check if range and objects are the same length
        assert len(objects_to_perceive) == len(range_to_perceive_them_in)

        # Create sense dictionary
        sense_dict = {}
        for idx, obj_class in enumerate(objects_to_perceive):
            perceive_range = range_to_perceive_them_in[idx]
            if perceive_range is None:
                perceive_range = np.inf
            sense_dict[obj_class] = perceive_range

        sense_capability = SenseCapability(sense_dict)

        return sense_capability

    def get_random_locations(self, nr_locations, area_corners=None):
        pass

    def get_random_property(self, property_name, values, nr=1, allow_duplicates=True):
        pass
