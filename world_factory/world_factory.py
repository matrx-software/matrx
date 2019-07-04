import inspect
import os
import sys
import warnings
from collections import OrderedDict
from typing import Callable
from noise import snoise2

import numpy as np
from numpy.random.mtrand import RandomState

from agents.agent import Agent
from agents.capabilities.capability import SenseCapability
from agents.human_agent import HumanAgent
from environment.gridworld import GridWorld
from environment.objects.agent_avatar import AgentAvatar
from environment.objects.env_object import EnvObject
from environment.objects.helper_functions import get_inheritence_path
from environment.objects.simple_objects import Wall, Door, AreaTile, SmokeTile
from environment.sim_goals.sim_goal import LimitedTimeGoal
from world_factory.helper_functions import get_default_value, _get_line_coords

######
# We do this so we are sure everything is imported and thus can be found
# noinspection PyUnresolvedReferences
import agents
# noinspection PyUnresolvedReferences
import agents.capabilities
# noinspection PyUnresolvedReferences
import environment
# noinspection PyUnresolvedReferences
import environment.sim_goals
# noinspection PyUnresolvedReferences
import environment.objects
# noinspection PyUnresolvedReferences
import environment.actions
# noinspection PyUnresolvedReferences
import environment.actions.door_actions
# noinspection PyUnresolvedReferences
import environment.actions.object_actions
# noinspection PyUnresolvedReferences
import environment.actions.move_actions
# noinspection PyUnresolvedReferences
import world_factory
# noinspection PyUnresolvedReferences
import visualization


######


class WorldFactory:

    def __init__(self, shape, tick_duration, random_seed=1, simulation_goal=1000, run_sail_api=True,
                 run_visualization_server=True, visualization_bg_clr="#C2C2C2"):
        """
        Create a WorldFactory who stores how you want the world to look like, and from which you can obtain infinite
        instantions of that world.
        :param shape: The grid size, (width, height)
        :param tick_duration: The duration of a tick in seconds.
        :param random_seed: The master random seed from which all other seeds are obtains
        :param simulation_goal: The goal that denotes when the simulation ended. Can be a SimulationGoal, a list of
         SimulationGoal, or an integer denoting the number of ticks the simulation runs.
        :param run_sail_api: Boolean if the SAIL api server should be started (not yet implemented)
        :param run_visualization_server: Boolean if the Visualisation server should be started (not yet implemented)
        """
        # Set our random number generator
        self.rng = np.random.RandomState(random_seed)
        # Set our settings place holders
        self.agent_settings = []
        self.object_settings = []

        # If simulation goal is an integer, we create a LimitedTimeGoal with that number of ticks
        if isinstance(simulation_goal, int):
            simulation_goal = LimitedTimeGoal(max_nr_ticks=simulation_goal)

        # Set our world settings
        self.world_settings = self.__set_world_settings(shape=shape,
                                                        tick_duration=tick_duration,
                                                        simulation_goal=simulation_goal,
                                                        run_sail_api=run_sail_api,
                                                        run_visualization_server=run_visualization_server,
                                                        visualization_bg_clr=visualization_bg_clr)
        # Keep track of the number of worlds we created
        self.worlds_created = 0

        # Set our custom warning method for all of the testbed
        def _warning(message, category, filename, lineno, file=None, line=None):
            filename = filename.split(os.sep)[-1].split(".")[0]
            if lineno is not None:
                print(f"{filename}@{lineno}:: {message}", file=sys.stderr)
            elif line is not None:
                print(f"{filename}@{line}:: {message}", file=sys.stderr)
            else:
                print(f"{filename}:: {message}", file=sys.stderr)

        warnings.showwarning = _warning

    def worlds(self, nr_of_worlds=10):
        while self.worlds_created < nr_of_worlds:
            yield self.get_world()

    def get_world(self):
        self.worlds_created += 1
        world = self.__create_world()
        self.__reset_random()
        return world

    def __set_world_settings(self, shape, tick_duration, simulation_goal, run_sail_api=True,
                             run_visualization_server=True, rnd_seed=None, visualization_bg_clr="#C2C2C2"):

        if rnd_seed is None:
            rnd_seed = self.rng.randint(0, 1000000)

        world_settings = {"shape": shape,
                          "tick_duration": tick_duration,
                          "simulation_goal": simulation_goal,
                          "run_sail_api": run_sail_api,
                          "run_visualization_server": run_visualization_server,
                          "rnd_seed": rnd_seed,
                          "visualization_bg_clr": visualization_bg_clr}

        return world_settings

    def add_agent(self, location, agent, name="Agent", customizable_properties=None, sense_capability=None,
                  is_traversable=None, team=None, agent_speed_in_ticks=None, possible_actions=None, is_movable=None,
                  visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_depth=None, visualize_opacity=None,
                  **custom_properties):

        # Check if location and agent are of correct type
        assert isinstance(location, list) or isinstance(location, tuple)
        assert isinstance(agent, Agent)

        # Load the defaults for any variable that is not defined
        # Obtain any defaults from the defaults.json file if not set already.
        if is_traversable is None:
            is_traversable = get_default_value(class_name="AgentAvatar", property_name="is_traversable")
        if visualize_size is None:
            visualize_size = get_default_value(class_name="AgentAvatar", property_name="visualize_size")
        if visualize_shape is None:
            visualize_shape = get_default_value(class_name="AgentAvatar", property_name="visualize_shape")
        if visualize_colour is None:
            visualize_colour = get_default_value(class_name="AgentAvatar", property_name="visualize_colour")
        if visualize_opacity is None:
            visualize_opacity = get_default_value(class_name="AgentAvatar", property_name="visualize_opacity")
        if visualize_depth is None:
            visualize_depth = get_default_value(class_name="AgentAvatar", property_name="visualize_depth")
        if agent_speed_in_ticks is None:
            agent_speed_in_ticks = get_default_value(class_name="AgentAvatar", property_name="agent_speed_in_ticks")
        if possible_actions is None:
            possible_actions = get_default_value(class_name="AgentAvatar", property_name="possible_actions")
        if is_movable is None:
            is_movable = get_default_value(class_name="AgentAvatar", property_name="is_movable")

        # If default variables are not given, assign them (most empty, except of sense_capability that defaults to all
        # objects with infinite range).
        if custom_properties is None:
            custom_properties = {}
        if sense_capability is None:
            sense_capability = self.create_sense_capability([], [])  # Create sense capability that perceives all
        if customizable_properties is None:
            customizable_properties = []

        # Check if the agent is not of HumanAgent, if so; use the add_human_agent method
        inh_path = get_inheritence_path(agent.__class__)
        if 'HumanAgent' in inh_path:
            Exception(f"You are adding an agent that is or inherits from HumanAgent with the name {name}. Use "
                      f"factory.add_human_agent to add such agents.")

        # Define a settings dictionary with all we need to register and add an agent to the GridWorld
        agent_setting = {"agent": agent,
                         "custom_properties": custom_properties,
                         "customizable_properties": customizable_properties,
                         "sense_capability": sense_capability,
                         "mandatory_properties": {
                             "name": name,
                             "is_movable": is_movable,
                             "is_traversable": is_traversable,
                             "possible_actions": possible_actions,
                             "is_human_agent": False,  # is you want a human agent, use factory.add_human_agent()
                             "agent_speed_in_ticks": agent_speed_in_ticks,
                             "visualize_size": visualize_size,
                             "visualize_shape": visualize_shape,
                             "visualize_colour": visualize_colour,
                             "visualize_opacity": visualize_opacity,
                             "visualize_depth": visualize_depth,
                             "location": location,
                             "team": team}
                         }

        self.agent_settings.append(agent_setting)

    def add_team(self, agents, locations, team_name, custom_properties=None, sense_capability=None,
                 customizable_properties=None, is_traversable=None, agent_speed_in_ticks=None,
                 visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_opacity=None):

        self.add_multiple_agents(agents, locations, custom_properties=custom_properties,
                                 sense_capabilities=sense_capability, customizable_properties=customizable_properties,
                                 is_traversable=is_traversable, agent_speeds_in_ticks=agent_speed_in_ticks,
                                 teams=team_name, visualize_sizes=visualize_size, visualize_shapes=visualize_shape,
                                 visualize_colours=visualize_colour, visualize_opacity=visualize_opacity)

    def add_multiple_agents(self, agents, locations, custom_properties=None,
                            sense_capabilities=None, customizable_properties=None,
                            is_traversable=None, agent_speeds_in_ticks=None,
                            teams=None, visualize_sizes=None, visualize_shapes=None,
                            visualize_colours=None, visualize_opacities=None, visualize_depths=None):

        # If any of the lists are not given, fill them with None and if they are a single value of its expected type we
        # copy it in a list. A none value causes the default value to be loaded.
        if custom_properties is None:
            custom_properties = [{} for _ in range(len(agents))]
        elif isinstance(custom_properties, dict):
            custom_properties = [custom_properties for _ in range(len(agents))]

        if sense_capabilities is None:
            sense_capabilities = [None for _ in range(len(agents))]
        elif isinstance(sense_capabilities, SenseCapability):
            sense_capabilities = [sense_capabilities for _ in range(len(agents))]

        if customizable_properties is None:
            customizable_properties = [None for _ in range(len(agents))]
        elif not any(isinstance(el, list) for el in customizable_properties):
            customizable_properties = [customizable_properties for _ in range(len(agents))]

        if is_traversable is None:
            is_traversable = [None for _ in range(len(agents))]
        elif isinstance(is_traversable, bool):
            is_traversable = [is_traversable for _ in range(len(agents))]

        if agent_speeds_in_ticks is None:
            agent_speeds_in_ticks = [None for _ in range(len(agents))]
        elif isinstance(agent_speeds_in_ticks, int):
            agent_speeds_in_ticks = [agent_speeds_in_ticks for _ in range(len(agents))]

        if teams is None:
            teams = [None for _ in range(len(agents))]
        elif isinstance(teams, str):
            teams = [teams for _ in range(len(agents))]

        if visualize_sizes is None:
            visualize_sizes = [None for _ in range(len(agents))]
        elif isinstance(visualize_sizes, int):
            visualize_sizes = [visualize_sizes for _ in range(len(agents))]

        if visualize_shapes is None:
            visualize_shapes = [None for _ in range(len(agents))]
        elif isinstance(visualize_shapes, int):
            visualize_shapes = [visualize_shapes for _ in range(len(agents))]

        if visualize_colours is None:
            visualize_colours = [None for _ in range(len(agents))]
        elif isinstance(visualize_colours, str):
            visualize_colours = [visualize_colours for _ in range(len(agents))]

        if visualize_opacities is None:
            visualize_opacities = [None for _ in range(len(agents))]
        elif isinstance(visualize_opacities, int):
            visualize_opacities = [visualize_opacities for _ in range(len(agents))]

        if visualize_depths is None:
            visualize_depths = [None for _ in range(len(agents))]
        elif isinstance(visualize_depths, int):
            visualize_depths = [visualize_depths for _ in range(len(agents))]

        # Loop through all agents and add them
        for idx, agent in enumerate(agents):
            self.add_agent(locations[idx], agent,
                           sense_capability=sense_capabilities[idx],
                           customizable_properties=customizable_properties[idx],
                           is_traversable=is_traversable[idx],
                           team=teams[idx],
                           agent_speed_in_ticks=agent_speeds_in_ticks[idx],
                           visualize_size=visualize_sizes[idx],
                           visualize_shape=visualize_shapes[idx],
                           visualize_colour=visualize_colours[idx],
                           visualize_depth=visualize_depths[idx],
                           visualize_opacity=visualize_opacities[idx],
                           **custom_properties[idx])

    def add_agent_prospect(self, location, agent, probability, name="Agent", customizable_properties=None,
                           sense_capability=None,
                           is_traversable=None, team=None, agent_speed_in_ticks=None, possible_actions=None,
                           is_movable=None,
                           visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_opacity=None,
                           visualize_depth=None, **custom_properties):

        # Add agent as normal
        self.add_agent(location, agent, name, customizable_properties, sense_capability,
                       is_traversable, team, agent_speed_in_ticks, possible_actions, is_movable,
                       visualize_size, visualize_shape, visualize_colour, visualize_depth,
                       visualize_opacity, **custom_properties)

        # Get the last settings (which we just added) and add the probability
        self.agent_settings[-1]['probability'] = probability

    def add_env_object(self, location, name, callable_class=None, customizable_properties=None,
                       is_traversable=None, is_movable=None,
                       visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_depth=None,
                       visualize_opacity=None, **custom_properties):
        if callable_class is None:
            callable_class = EnvObject

        # Check if location and agent are of correct type
        assert isinstance(location, list) or isinstance(location, tuple)
        assert isinstance(callable_class, Callable)

        # Load default parameters if not passed
        if is_movable is None:
            is_movable = get_default_value(class_name="EnvObject", property_name="is_movable")

        # If default variables are not given, assign them (most empty, except of sense_capability that defaults to all
        # objects with infinite range).
        if custom_properties is None:
            custom_properties = {}
        if customizable_properties is None:
            customizable_properties = []

        # Define a settings dictionary with all we need to register and add an agent to the GridWorld
        object_setting = {"callable_class": callable_class,
                          "custom_properties": custom_properties,
                          "customizable_properties": customizable_properties,
                          "mandatory_properties": {
                              "name": name,
                              "is_traversable": is_traversable,
                              "visualize_size": visualize_size,
                              "visualize_shape": visualize_shape,
                              "visualize_colour": visualize_colour,
                              "visualize_depth": visualize_depth,
                              "visualize_opacity": visualize_opacity,
                              "is_movable": is_movable,
                              "location": location}
                          }
        self.object_settings.append(object_setting)

    def add_env_object_prospect(self, location, name, probability, callable_class=None, customizable_properties=None,
                                is_traversable=None,
                                visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_depth=None,
                                visualize_opacity=None, **custom_properties):
        # Add object as normal
        self.add_env_object(location, name, callable_class, customizable_properties,
                            is_traversable,
                            visualize_size, visualize_shape, visualize_colour, visualize_depth,
                            visualize_opacity, **custom_properties)

        # Get the last settings (which we just added) and add the probability
        self.object_settings[-1]['probability'] = probability

    def add_multiple_objects(self, locations, names=None, callable_classes=None, custom_properties=None,
                             customizable_properties=None, is_traversable=None, visualize_sizes=None,
                             visualize_shapes=None, visualize_colours=None, visualize_depths=None,
                             visualize_opacities=None, is_movable=None):

        # If any of the lists are not given, fill them with None and if they are a single value of its expected type we
        # copy it in a list. A none value causes the default value to be loaded.
        if names is None:
            names = [None for _ in range(len(locations))]
        elif isinstance(names, str):
            names = [names for _ in range(len(locations))]

        if is_movable is None:
            is_movable = [None for _ in range(len(locations))]
        elif isinstance(is_movable, bool):
            is_movable = [is_movable for _ in range(len(locations))]

        if callable_classes is None:
            callable_classes = [EnvObject for _ in range(len(locations))]
        elif isinstance(callable_classes, Callable):
            callable_classes = [callable_classes for _ in range(len(locations))]

        if custom_properties is None:
            custom_properties = [{} for _ in range(len(locations))]
        elif isinstance(custom_properties, dict):
            custom_properties = [custom_properties for _ in range(len(locations))]

        if customizable_properties is None:
            customizable_properties = [None for _ in range(len(locations))]
        elif not any(isinstance(el, list) for el in customizable_properties):
            customizable_properties = [customizable_properties for _ in range(len(locations))]

        if is_traversable is None:
            is_traversable = [None for _ in range(len(locations))]
        elif isinstance(is_traversable, bool):
            is_traversable = [is_traversable for _ in range(len(locations))]

        if visualize_sizes is None:
            visualize_sizes = [None for _ in range(len(locations))]
        elif isinstance(visualize_sizes, int):
            visualize_sizes = [visualize_sizes for _ in range(len(locations))]

        if visualize_shapes is None:
            visualize_shapes = [None for _ in range(len(locations))]
        elif isinstance(visualize_shapes, int):
            visualize_shapes = [visualize_shapes for _ in range(len(locations))]

        if visualize_colours is None:
            visualize_colours = [None for _ in range(len(locations))]
        elif isinstance(visualize_colours, str):
            visualize_colours = [visualize_colours for _ in range(len(locations))]

        if visualize_opacities is None:
            visualize_opacities = [None for _ in range(len(locations))]
        elif isinstance(visualize_opacities, int):
            visualize_opacities = [visualize_opacities for _ in range(len(locations))]

        if visualize_depths is None:
            visualize_depths = [None for _ in range(len(locations))]
        elif isinstance(visualize_depths, str):
            visualize_depths = [visualize_depths for _ in range(len(locations))]

        # Loop through all agents and add them
        for idx in range(len(locations)):
            self.add_env_object(location=locations[idx], name=names[idx], callable_class=callable_classes[idx],
                                customizable_properties=customizable_properties[idx],
                                is_traversable=is_traversable[idx], is_movable=is_movable[idx],
                                visualize_size=visualize_sizes[idx], visualize_shape=visualize_shapes[idx],
                                visualize_colour=visualize_colours[idx], visualize_depth=visualize_depths[idx],
                                visualize_opacity=visualize_opacities[idx], **custom_properties[idx])

    def add_human_agent(self, location, agent, name="HumanAgent", customizable_properties=None, sense_capability=None,
                        is_traversable=None, team=None, agent_speed_in_ticks=None, possible_actions=None,
                        is_movable=None,
                        visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_depth=None,
                        visualize_opacity=None, usrinp_action_map=None, **custom_properties):

        # Check if location and agent are of correct type
        assert isinstance(location, list) or isinstance(location, tuple)
        assert isinstance(agent, HumanAgent)

        # Load the defaults for any variable that is not defined
        # Obtain any defaults from the defaults.json file if not set already.
        if is_traversable is None:
            is_traversable = get_default_value(class_name="AgentAvatar", property_name="is_traversable")
        if visualize_size is None:
            visualize_size = get_default_value(class_name="AgentAvatar", property_name="visualize_size")
        if visualize_shape is None:
            visualize_shape = get_default_value(class_name="AgentAvatar", property_name="visualize_shape")
        if visualize_colour is None:
            visualize_colour = get_default_value(class_name="AgentAvatar", property_name="visualize_colour")
        if visualize_opacity is None:
            visualize_opacity = get_default_value(class_name="AgentAvatar", property_name="visualize_opacity")
        if visualize_depth is None:
            visualize_depth = get_default_value(class_name="AgentAvatar", property_name="visualize_depth")
        if agent_speed_in_ticks is None:
            agent_speed_in_ticks = get_default_value(class_name="AgentAvatar", property_name="agent_speed_in_ticks")
        if possible_actions is None:
            possible_actions = get_default_value(class_name="AgentAvatar", property_name="possible_actions")
        if is_movable is None:
            is_movable = get_default_value(class_name="AgentAvatar", property_name="is_movable")

        # If default variables are not given, assign them (most empty, except of sense_capability that defaults to all
        # objects with infinite range).
        if custom_properties is None:
            custom_properties = {}
        if sense_capability is None:
            sense_capability = self.create_sense_capability([], [])  # Create sense capability that perceives all
        if customizable_properties is None:
            customizable_properties = []

        # Check if the agent is of HumanAgent, if not; use the add_agent method
        inh_path = get_inheritence_path(agent.__class__)
        if 'HumanAgent' not in inh_path:
            Exception(f"You are adding an agent that does not inherit from HumanAgent with the name {name}. Use "
                      f"factory.add_agent to add autonomous agents.")

        # Append the user input map to the custom properties
        custom_properties["usrinp_action_map"] = usrinp_action_map

        # Define a settings dictionary with all we need to register and add an agent to the GridWorld
        hu_ag_setting = {"agent": agent,
                         "custom_properties": custom_properties,
                         "customizable_properties": customizable_properties,
                         "sense_capability": sense_capability,
                         "mandatory_properties": {
                             "name": name,
                             "is_movable": is_movable,
                             "is_traversable": is_traversable,
                             "possible_actions": possible_actions,
                             "is_human_agent": True,
                             "agent_speed_in_ticks": agent_speed_in_ticks,
                             "visualize_size": visualize_size,
                             "visualize_shape": visualize_shape,
                             "visualize_colour": visualize_colour,
                             "visualize_opacity": visualize_opacity,
                             "visualize_depth": visualize_depth,
                             "location": location,
                             "team": team}
                         }

        self.agent_settings.append(hu_ag_setting)

    def add_area(self, top_left_location, width, height, name, customizable_properties=None, visualize_colour=None,
                 visualize_opacity=None, **custom_properties):
        # Check if width and height are large enough to make an actual room (with content)
        if width < 1 or height < 1:
            raise Exception(f"While adding area {name}; The width {width} and/or height {height} should both be larger"
                            f" than 0.")

        # Get all locations in the rectangle
        locs = self.__list_area_locs(top_left_location, width, height)

        # Add all area objects
        self.add_multiple_objects(locations=locs, callable_classes=AreaTile,
                                  customizable_properties=customizable_properties, visualize_colours=visualize_colour,
                                  visualize_opacities=visualize_opacity, **custom_properties)


    def add_smoke_area(self, top_left_location, width, height, name, visualize_colour=None,
                 smoke_thickness_multiplier=1.0, visualize_depth=None, **custom_properties):
        # Check if width and height are large enough to make an actual room (with content)
        if width < 1 or height < 1:
            raise Exception(f"While adding area {name}; The width {width} and/or height {height} should both be larger"
                            f" than 0.")

        # See https://www.redblobgames.com/maps/terrain-from-noise/#elevation
        octaves = 8 # small noiseyness
        freq = 5 # large noiseyness

        # Get all locations in the rectangle
        min_x = top_left_location[0]
        max_x = top_left_location[0] + width
        min_y = top_left_location[1]
        max_y = top_left_location[1] + height

        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                # get noise point
                noise = snoise2(x / freq, y / freq, octaves)

                # convert from [-1,1] range to [0,1] range, and flip
                opacity = 1 - ((noise + 1.0) / 2.0)
                opacity = np.clip(opacity * smoke_thickness_multiplier, 0, 1)

                # add the smokeTile
                self.add_env_object(location=[x,y], name=name, callable_class=SmokeTile, visualize_colour=visualize_colour, visualize_opacity=opacity, visualize_depth=visualize_depth)




    def __list_area_locs(self, top_left_location, width, height):
        """
        Provided an area with the top_left_location, width and height,
        generate a list containing all coordinates in that area
        """

        # Get all locations in the rectangle
        locs = []
        min_x = top_left_location[0]
        max_x = top_left_location[0] + width
        min_y = top_left_location[1]
        max_y = top_left_location[1] + height

        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                locs.append((x, y))

        return locs


    def add_line(self, start, end, name, callable_class=None, customizable_properties=None,
                 is_traversable=None, is_movable=None,
                 visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_depth=None,
                 visualize_opacity=None, **custom_properties):

        # Get the coordinates on the given line
        line_coords = _get_line_coords(start, end)

        # Construct the names
        names = [name for _ in line_coords]

        # Add the actual properties
        self.add_multiple_objects(locations=line_coords, names=names, callable_classes=callable_class,
                                  custom_properties=custom_properties, customizable_properties=customizable_properties,
                                  is_traversable=is_traversable, visualize_sizes=visualize_size,
                                  visualize_shapes=visualize_shape, visualize_colours=visualize_colour,
                                  visualize_opacities=visualize_opacity, visualize_depths=visualize_depth, is_movable=is_movable)

    def add_room(self, top_left_location, width, height, name, door_locations=None, with_area_tiles=False,
                 doors_open=False,
                 wall_custom_properties=None, wall_customizable_properties=None,
                 area_custom_properties=None, area_customizable_properties=None,
                 area_visualize_colour=None, area_visualize_opacity=None):

        # Check if width and height are large enough to make an actual room (with content)
        if width <= 2 or height <= 2:
            raise Exception(f"While adding room {name}; The width {width} and/or height {height} should both be larger"
                            f" than 2.")

        # Check if the with_area boolean is True when any area properties are given
        if with_area_tiles is False and (
                area_custom_properties is not None or
                area_customizable_properties is not None or
                area_visualize_colour is not None or
                area_visualize_opacity is not None):
            warnings.warn(f"While adding room {name}: The boolean with_area_tiles is set to {with_area_tiles} while "
                          f"also providing specific area statements. Treating with_area_tiles as True.")
            with_area_tiles = True

        # Subtract 1 from both width and height, since the top left already counts as a size of 1,1
        width -= 1
        height -= 1

        # Set corner coordinates
        top_left = top_left_location
        top_right = (top_left_location[0] + width, top_left_location[1])
        bottom_left = (top_left_location[0], top_left_location[1] + height)
        bottom_right = (top_left_location[0] + width, top_left_location[1] + height)

        # Get all edge coordinates
        top = _get_line_coords(top_left, top_right)
        right = _get_line_coords(top_right, bottom_right)
        bottom = _get_line_coords(bottom_left, bottom_right)
        left = _get_line_coords(top_left, bottom_left)

        # Combine in one and remove duplicates
        all_ = top
        all_.extend(right)
        all_.extend(bottom)
        all_.extend(left)
        all_ = list(set(all_))

        # Check if all door locations are at wall locations, if so remove those wall locations
        door_locations = None if door_locations is None else door_locations
        for door_loc in door_locations:
            if door_loc in all_:
                all_.remove(door_loc)
            else:
                raise Exception(f"While adding room {name}, the requested door location {door_loc} is not in a wall.")

        # Add all walls
        names = [f"{name} - wall@{loc}" for loc in all_]
        self.add_multiple_objects(locations=all_, names=names, callable_classes=Wall,
                                  custom_properties=wall_custom_properties,
                                  customizable_properties=wall_customizable_properties)

        # Add all doors
        for door_loc in door_locations:
            self.add_env_object(location=door_loc, name=f"{name} - door@{door_loc}", callable_class=Door,
                                is_open=doors_open)

        # Add all area tiles if required
        if with_area_tiles:
            area_top_left = (top_left[0] + 1, top_left[1] + 1)
            area_width = width - 1
            area_height = height - 1

            # If properties happens to be none, set it to empty dict
            if area_custom_properties is None:
                area_custom_properties = {}

            self.add_area(top_left_location=area_top_left, width=area_width, height=area_height, name=f"{name}_area",
                          visualize_colour=area_visualize_colour, visualize_opacity=area_visualize_opacity,
                          customizable_properties=area_customizable_properties, **area_custom_properties)

    def create_sense_capability(self, objects_to_perceive, range_to_perceive_them_in):
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

    def __create_world(self):

        # Create the world
        world = self.__create_grid_world()

        # Create all objects first
        objs = []
        for obj_settings in self.object_settings:
            env_object = self.__create_env_object(obj_settings)
            if env_object is not None:
                objs.append(env_object)

        # Then create all agents
        avatars = []
        for agent_settings in self.agent_settings:
            agent, agent_avatar = self.__create_agent_avatar(agent_settings)
            if agent_avatar is not None:
                avatars.append((agent, agent_avatar))

        # Register all objects (including checks)
        for env_object in objs:
            world.register_env_object(env_object)

        # Register all agents (including checks)
        for agent, agent_avatar in avatars:
            world.register_agent(agent, agent_avatar)

        # Return the (successful/stable) world
        return world

    def __create_grid_world(self):
        args = self.world_settings
        world = GridWorld(**args)
        return world

    def __create_env_object(self, settings):

        # First we check if this settings represent a probabilistic object, because then we expect settings to contain
        # a probability setting.
        if 'probability' in settings.keys():
            prob = settings['probability']
            p = self.rng.rand()
            if p > prob:
                return None

        callable_class = settings['callable_class']
        custom_props = settings['custom_properties']
        customizable_props = settings['customizable_properties']
        mandatory_props = settings['mandatory_properties']

        if callable_class == EnvObject:  # If it is a 'normal' EnvObject we do not treat it differently
            # Collect all arguments in a dictionary
            args = {'location': mandatory_props['location'],
                    'name': mandatory_props['name'],
                    'class_callable': callable_class,
                    'customizable_properties': customizable_props,
                    'is_traversable': mandatory_props['is_traversable'],
                    'visualize_size': mandatory_props['visualize_size'],
                    'visualize_shape': mandatory_props['visualize_shape'],
                    'visualize_colour': mandatory_props['visualize_colour'],
                    'visualize_opacity': mandatory_props['visualize_opacity'],
                    'visualize_depth': mandatory_props['visualize_depth'],
                    **custom_props}

        else:  # else we need to check what this object's constructor requires and obtain those properties only
            # Get all variables required by constructor
            argspecs = inspect.getargspec(callable_class)
            args = argspecs.args  # does not give *args or **kwargs names
            defaults = argspecs.defaults  # defaults (if any) of the last n elements in args

            # Now assign the default values to kwargs dictionary
            args = OrderedDict({arg: "not_set" for arg in reversed(args[1:])})
            if defaults is not None:
                for idx, default in enumerate(reversed(defaults)):
                    k = list(args.keys())[idx]
                    args[k] = default

            # Check if all arguments are present (fails if a required argument without a default value is not given)
            for arg, default in args.items():
                if arg not in custom_props.keys() and arg not in mandatory_props.keys() and default == "not_set":
                    raise Exception(f"Cannot create environment object of type {callable_class.__name__} with name "
                                    f"{mandatory_props['name']}, as its constructor requires the argument named {arg} "
                                    f"which is not given as a property.")
                elif arg in custom_props.keys() and custom_props[arg] is not None:
                    # an argument is present in custom_props, which overrides constructor defaults
                    args[arg] = custom_props[arg]
                elif arg in mandatory_props.keys() and mandatory_props[arg] is not None:
                    # an argument is present in mandatory_props, which overrides constructor defaults
                    args[arg] = mandatory_props[arg]

            # We provide a warning if some custom properties are given which are not used for this class
            not_used = [prop_name for prop_name in custom_props.keys() if prop_name not in args.keys()]
            if len(not_used) > 0:
                warnings.warn(f"The following properties are not used in the creation of environment object of type "
                              f"{callable_class.__name__} with name {mandatory_props['name']}; {not_used}")

        args = self.__instantiate_random_properties(args)
        env_object = callable_class(**args)

        return env_object

    def __create_agent_avatar(self, settings):

        agent = settings['agent']

        # First we check if this settings represent a probabilistic object, because then we expect settings to contain
        # a probability setting.
        if 'probability' in settings.keys():
            prob = settings['probability']
            p = self.rng.rand()
            if p > prob:
                return agent, None

        sense_capability = settings['sense_capability']
        custom_props = settings['custom_properties']
        customizable_props = settings['customizable_properties']
        mandatory_props = settings['mandatory_properties']

        args = {**mandatory_props,
                'sense_capability': sense_capability,
                'class_callable': agent.__class__,
                'callback_agent_get_action': agent.get_action,
                'callback_agent_set_action_result': agent.set_action_result,
                'callback_agent_observe': agent.ooda_observe,
                'callback_agent_get_messages': agent.get_messages,
                'callback_agent_set_messages': agent.set_messages,
                'customizable_properties': customizable_props,
                **custom_props}

        # Parse arguments and create the AgentAvatar
        args = self.__instantiate_random_properties(args)
        avatar = AgentAvatar(**args)

        # We return the agent and avatar (as we will complete the initialisation of the agent when we register it)
        return agent, avatar

    def __instantiate_random_properties(self, args):
        # Checks if all given arguments in the dictionary are not None, and if they are of RandomProperty or
        # RandomLocation, their (random) value is retrieved.
        for k, v in args.items():
            if isinstance(v, RandomProperty):
                args[k] = v.get_property(self.rng)
            elif isinstance(v, RandomLocation):
                args[k] = v.get_location(self.rng)

        return args

    def __reset_random(self):
        # TODO resets all RandomProperty and RandomLocation, is called after creating a world so all duplicates can be
        # TODO selected again.
        pass


class RandomProperty:

    def __init__(self, values, distribution=None, allow_duplicates=True):

        # If distribution is None, its uniform (equal probability to all values)
        if distribution is None:
            distribution = [1 / len(values) for _ in range(values)]

        # Normalize distribution if not already
        if sum(distribution) != 1.0:
            distribution = [el / sum(distribution) for el in distribution]

        # Check that the distribution is complete
        assert len(distribution) == len(values)

        # Assign values and distribution
        self.values = values
        self.distribution = distribution
        self.allow_duplicates = allow_duplicates
        self.selected_values = set()

    def get_property(self, rng: RandomState, size=None):
        vals = self.values.copy()
        if not self.allow_duplicates:
            for it in self.selected_values:
                vals.remove(it)
        choice = rng.choice(vals, p=self.distribution, size=size, replace=self.allow_duplicates)
        self.selected_values.add(choice)
        return choice

    def reset(self):
        self.selected_values = set()


class RandomLocation:

    def __init__(self, area_corners):
        self.area_corners = area_corners

    def get_location(self, rng):
        # TODO
        pass

    def reset(self):
        # TODO
        pass
