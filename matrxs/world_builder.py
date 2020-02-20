import inspect
import os
import sys
import warnings
from collections import OrderedDict
from typing import Callable, Union, Iterable
import requests

import numpy as np
from numpy.random.mtrand import RandomState

from matrxs.agents.agent_brain import AgentBrain
from matrxs.agents.capabilities.capability import SenseCapability
from matrxs.agents.human_agent_brain import HumanAgentBrain
from matrxs.grid_world import GridWorld
from matrxs.logger.logger import GridWorldLogger
from matrxs.objects.agent_body import AgentBody
from matrxs.objects.env_object import EnvObject
from matrxs.utils import utils
from matrxs.utils.utils import get_inheritence_path, get_default_value, _get_line_coords, create_sense_capability
from matrxs.objects.simple_objects import Wall, Door, AreaTile, SmokeTile
from matrxs.sim_goals.sim_goal import LimitedTimeGoal, SimulationGoal

# addons
from matrxs.API import api
from matrxs_visualizer import visualization_server

class WorldBuilder:

    def __init__(self, shape, tick_duration=0.5, random_seed=1, simulation_goal=1000, run_matrxs_api=True,
                 run_matrxs_visualizer=False, visualization_bg_clr="#C2C2C2", visualization_bg_img=None,
                 verbose=False):
        """
        A builder to create one or more worlds.

        With the constructor you can set a number of general properties and from the resulting instance you can call
        numerous methods to add new objects and/or agents.

        Parameters
        ----------
        shape : tuple
            Denotes the width and height of the world you create.
        tick_duration : float, optional
            The duration of a single 'tick' or loop in the game-loop of the world you create. Defaults to 0.5.
        random_seed : int, optional
            The master random seed on which all objects, agents and worlds are seeded. Should be a positive non-zero
            integer. Defaults 1.0.
        simulation_goal : int, SimulationGoal, list of SimulationGoal, optional
            The goal or goals of the world, either a single SimulationGoal, a list of such or a positive non-zero
            integer to denote the maximum number of 'ticks' the world(s) have to run. Defaults to 1000.
        run_matrxs_api : bool, optional
            Whether to run the MATRXS API
        run_matrxs_visualizer : bool, optional
            Whether to run the default MATRXS visualizer, this requires the API to be run
        visualization_bg_clr : str, optional
            The color of the world when visualized using MATRXS' own visualisation server. A string representation of
            hexadecimal color. Defaults to "#C2C2C2" (light grey).
        visualization_bg_img : str, optional
            An optional background image of the world when visualized using MATRXS' own visualisation server. A string
            of the path to the image file. Defaults to None (no image).
        verbose : bool, optional
            Whether the subsequent created world should be verbose or not. Defaults to False.

        Raises
        ------
        ValueError
            On an incorrect argument. The exception specifies further what argument and what is erroneous about it.

        Examples
        --------

        This creates a WorldBuilder that creates world of a certain size (here 10 by 10);

            >>> from matrxs.world_builder import WorldBuilder
            >>> WorldBuilder(shape=(10, 10))

        To create a WorldBuilder with a black background, a tick duration as fast as possible and with a different
        master random seed;

            >>> from matrxs.world_builder import WorldBuilder
            >>> WorldBuilder(shape=(10, 10), random_seed=42, tick_duration=-1, visualization_bg_clr="#000000")

        """

        # Check if shape is of correct type and length
        if not isinstance(shape, list) and not isinstance(shape, tuple) and len(shape) != 2:
            raise ValueError(f"The given grid shape {shape} is not of type List, Tuple or of length two.")

        # convert int to float
        if isinstance(tick_duration, int):
            tick_duration = float(tick_duration)

        # Check that tick duration is of float and a positive number.
        if not isinstance(tick_duration, float) and tick_duration >= 0.0:
            raise ValueError(f"The given tick_duration {tick_duration} should be a Float and larger or equal than 0.0.")

        # Check that the random seed is a positive non-zero integer
        if not isinstance(random_seed, int) and random_seed > 0:
            raise ValueError(f"The given random_seed {random_seed} should be an Int and bigger or equal to 1.")

        # Check if the simulation_goal is a SimulationGoal, an int or a list or tuple of SimulationGoal
        if not isinstance(simulation_goal, SimulationGoal) and not isinstance(simulation_goal, int) \
                and not (isinstance(simulation_goal, Iterable) and (sum(1 for _ in simulation_goal)) > 0):
            raise ValueError(f"The given simulation_goal {simulation_goal} should be of type {SimulationGoal.__name__} "
                             f"or a list/tuple of {SimulationGoal.__name__}, or it should be an int denoting the max"
                             f"number of ticks the world should run (negative for infinite).")

        # Check the background color
        if not isinstance(visualization_bg_clr, str) and len(visualization_bg_clr) != 7 and \
                visualization_bg_clr[0] is not "#":
            raise ValueError(f"The given visualization_bg_clr {visualization_bg_clr} should be a Str of length 7 with"
                             f"an initial '#'' (a hexidecimal color string).")

        # Check if the background image is a path
        if visualization_bg_img is not None and not isinstance(visualization_bg_img, str):
            raise ValueError(f"The given visualization_bg_img {visualization_bg_img} should be of type str denoting a path"
                             f" to an image.")

        if not isinstance(run_matrxs_visualizer, bool):
            raise ValueError(f"The given value {run_matrxs_visualizer} for run_matrxs_visualizer is invalid, should be "
                             f"of type bool ")

        if not isinstance(run_matrxs_api, bool):
            raise ValueError(f"The given value {run_matrxs_api} for run_matrxs_api is invalid, should be "
                             f"of type bool.")

        if not run_matrxs_api and run_matrxs_visualizer:
            raise ValueError(f"Run_matrxs_api is set to False while run_matrxs_visualizer is set to True. The MATRXS "
                             f"visualizer requires the API to work, so this is not possible.")

        # Set our random number generator
        self.rng = np.random.RandomState(random_seed)
        # Set our settings place holders
        self.agent_settings = []
        self.object_settings = []
        # Set our logger place holders
        self.loggers = []

        # initialize an API variables
        self.run_matrxs_api = run_matrxs_api
        self.api_info = {   "run_matrxs_api": run_matrxs_api,
                            "api_thread": False }

        # initialize the visualization variables
        self.run_matrxs_visualizer = run_matrxs_visualizer
        self.matrxs_visualizer_thread = False

        # Whether the world factory and evrything else should print stuff
        self.verbose = verbose

        # If simulation goal is an integer, we create a LimitedTimeGoal with that number of ticks
        if isinstance(simulation_goal, int):
            simulation_goal = LimitedTimeGoal(max_nr_ticks=simulation_goal)

        # Set our world settings
        self.world_settings = self.__set_world_settings(shape=shape,
                                                        tick_duration=tick_duration,
                                                        simulation_goal=simulation_goal,
                                                        visualization_bg_clr=visualization_bg_clr,
                                                        visualization_bg_img=visualization_bg_img,
                                                        verbose=self.verbose,
                                                        rnd_seed=random_seed)
        # Keep track of the number of worlds we created
        self.worlds_created = 0

        # Based on our verbosity and debug level, we set a warning scheme
        if verbose:
            warnings.simplefilter("always")
        else:  # use the default (print all warnings once per location [module and line number])
            warnings.simplefilter("default")


    def worlds(self, nr_of_worlds: int = 100):
        """
        Returns a Generator of GridWorld instance for the specified number of worlds.

        Parameters
        ----------
        nr_of_worlds
            The number of worlds the Generator contains. Defaults to 10.

        Yields
        ------
        GridWorld
            A GridWorld, where all random properties and prospects are sampled using the given master seed.

        Raises
        ------
        ValueError
            The nr_of_worlds should be a postive non-zero integer.

        """

        if not isinstance(nr_of_worlds, int) and nr_of_worlds <= 0:
            raise ValueError(f"The given nr_of_worlds {nr_of_worlds} should be of type Int and larger or equal to 1.")

        while self.worlds_created < nr_of_worlds:
            yield self.get_world()

    def get_world(self):
        """
        Creates a single GridWorld instance based on the current state of this WorldFactor instance.

        The returned GridWorld can be started with world.run().

        Returns
        -------
        world: GridWorld
            A GridWorld instance.

        See Also
        --------

        """
        #TODO Refer to GridWorld.run()
        self.worlds_created += 1
        world = self.__create_world()
        self.__reset_random()
        return world

    def __set_world_settings(self, shape, tick_duration, simulation_goal,  rnd_seed,
                             visualization_bg_clr, visualization_bg_img, verbose):

        if rnd_seed is None:
            rnd_seed = self.rng.randint(0, 1000000)

        world_settings = {"shape": shape,
                          "tick_duration": tick_duration,
                          "simulation_goal": simulation_goal,
                          "rnd_seed": rnd_seed,
                          "visualization_bg_clr": visualization_bg_clr,
                          "visualization_bg_img": visualization_bg_img,
                          "verbose": verbose}

        return world_settings

    def add_logger(self, logger_class, log_strategy=None, save_path=None, file_name=None,
                   file_extension=None, delimiter=None, **kwargs):

        if issubclass(logger_class, GridWorldLogger):

            set_params = {'log_strategy': log_strategy, 'save_path': save_path, 'file_name': file_name,
                          'file_extension': file_extension, 'delimiter': delimiter}

            # Add all kwarg
            set_params = {**set_params, **kwargs}

            # Get the variables this logger class needs, and ignore the rest
            accepted_parameters = {}
            class_signature = inspect.signature(logger_class.__init__)
            class_params = class_signature.parameters
            for param in class_params.values():
                if param.name in set_params.keys():
                    if set_params[param.name] is not None:
                        accepted_parameters[param.name] = set_params[param.name]
                    else:
                        accepted_parameters[param.name] = param.default

            # Append the class and its parameters to the list of loggers
            self.loggers.append((logger_class, accepted_parameters))
        else:
            raise Exception(f"The logger is not of type, nor inherits from, {GridWorldLogger.__name__}.")

    def add_agent(self, location: Union[tuple, list], agent_brain: AgentBrain, name,
                  customizable_properties: Union[tuple, list] = None, sense_capability: SenseCapability = None,
                  is_traversable: bool = True, team: str = None, possible_actions: list = None, is_movable: bool = None,
                  visualize_size: float = None, visualize_shape: Union[float, str] = None, visualize_colour: str = None,
                  visualize_depth: int = None, visualize_opacity: float = None,
                  **custom_properties):
        """The helper method within a WorldFactory instance to add a single agent.

        This method makes sure that when this
        factory generates a GridWorld instance, it contains an AgentBody connected to the given AgentBrain.

        All keyword parameters default to None. Which means that their values are obtained from the
        "scenarios/defaults.json" file under the segment AgentBody.

        Parameters
        ----------
        location
            The location (x,y) of the to be added agent.
        agent_brain
            The AgentBrain instance that will control the agent.
        name
            The name of the agent, should be unique to allow the visualisation to have a single web page per agent. If
            the name is already used, an exception is thrown.
        customizable_properties: optional
            A list or tuple of names of properties for this agent that can be altered or customized. Either by the agent
            itself or by other agents or objects. If a property value gets changed that is not in this list than an
            exception is thrown.
        sense_capability: optional
            The SenseCapability object belonging this this agent's AgentBody. Used by the GridWorld to pre-filter
            objects and agents from this agent's states when querying for actions. Defaults to a SenseCapability that
            sees all object types within the entire world.
        is_traversable: optional
            Denotes whether other agents and object can move over this agent. It also throws an exception when this is
            set to False and another object/agent with this set to False is added to the same location.
        team: optional
            The team name. Used to group agents together. Defaults to this agent's name + "_team" to signify it
            forms its own team.
        possible_actions: optional
            A list or tuple of the names of the Action classes this agent can perform. With this you can limit the
            actions this agent can perform.
        is_movable: optional
            Whether this agent can be moved by other agents (currently this only happens with the DropObjectAction and
            PickUpAction).
        visualize_size: optional
            The size of this agent in its visualisation. A value of 1.0 denotes the full grid location square, whereas
            a value of 0.5 denotes half, and 0.0 an infinitesimal small size.
        visualize_shape: optional
            The shape of this agent in its visualisation. Depending on the value it obtains this shape: 0 = a square,
            1 = a triangle, 2 = a circle or when "img" the image from `image_filename` is used.
        visualize_colour: optional
            The colour of this agent in its visualisation. Should be a string hexadecimal colour value.
        visualize_depth: optional
            The visualisation depth of this agent in its visualisation. It denotes the 'layer' on which it is
            visualized. A larger value is more on 'top'.
        visualize_opacity: optional
            The opacity of this agent in its visualization. A value of 1.0 means full opacity and 0.0 no opacity.
        custom_properties: optional
            Any additional given keyword arguments will be encapsulated in this dictionary. These will be added to the
            AgentBody as custom_properties which can be perceived by other agents and objects or which can be used or
            altered (if allowed to by the customizable_properties list) by the AgentBrain or others.

        Returns
        -------
        None
            ...

        Raises
        ------
        AttributeError
            When the given agent name is already added to this WorldFactory instance.

        """

        # Check if location and agent are of correct type
        if not isinstance(location, list) and not isinstance(location, tuple) and len(location) != 2:
            raise ValueError(f"The given location {location} while adding the agent with name {name} is not a list, "
                             f"tuple or  of length two.")

        if not isinstance(agent_brain, AgentBrain):
            raise ValueError(f"The given agent_brain while adding agent with name {name} is not of type "
                             f"{AgentBrain.__name__} but of type {agent_brain.__class__.__name__}.")

        # Check if the agent name is unique
        for existingAgent in self.agent_settings:
            if existingAgent["mandatory_properties"]["name"] == name:
                raise ValueError(f"An agent with the name {name} was already added. Agent names should be unique.",
                                 name)

        # Load the defaults for any variable that is not defined
        # Obtain any defaults from the defaults.json file if not set already.
        if is_traversable is None:
            is_traversable = get_default_value(class_name="AgentBody", property_name="is_traversable")
        if visualize_size is None:
            visualize_size = get_default_value(class_name="AgentBody", property_name="visualize_size")
        if visualize_shape is None:
            visualize_shape = get_default_value(class_name="AgentBody", property_name="visualize_shape")
        if visualize_colour is None:
            visualize_colour = get_default_value(class_name="AgentBody", property_name="visualize_colour")
        if visualize_opacity is None:
            visualize_opacity = get_default_value(class_name="AgentBody", property_name="visualize_opacity")
        if visualize_depth is None:
            visualize_depth = get_default_value(class_name="AgentBody", property_name="visualize_depth")
        if possible_actions is None:
            possible_actions = get_default_value(class_name="AgentBody", property_name="possible_actions")
        if is_movable is None:
            is_movable = get_default_value(class_name="AgentBody", property_name="is_movable")

        # If default variables are not given, assign them (most empty, except of sense_capability that defaults to all
        # objects with infinite range).
        if custom_properties is None:
            custom_properties = {}
        if sense_capability is None:
            sense_capability = create_sense_capability([], [])  # Create sense capability that perceives all
        if customizable_properties is None:
            customizable_properties = []

        # Check if the agent is not of HumanAgent, if so; use the add_human_agent method
        inh_path = get_inheritence_path(agent_brain.__class__)
        if 'HumanAgent' in inh_path:
            Exception(f"You are adding an agent that is or inherits from HumanAgent with the name {name}. Use "
                      f"factory.add_human_agent to add such agents.")

        # Define a settings dictionary with all we need to register and add an agent to the GridWorld
        agent_setting = {"agent": agent_brain,
                         "custom_properties": custom_properties,
                         "customizable_properties": customizable_properties,
                         "sense_capability": sense_capability,
                         "mandatory_properties": {
                             "name": name,
                             "is_movable": is_movable,
                             "is_traversable": is_traversable,
                             "possible_actions": possible_actions,
                             "is_human_agent": False,  # is you want a human agent, use factory.add_human_agent()
                             "visualize_size": visualize_size,
                             "visualize_shape": visualize_shape,
                             "visualize_colour": visualize_colour,
                             "visualize_opacity": visualize_opacity,
                             "visualize_depth": visualize_depth,
                             "location": location,
                             "team": team}
                         }

        self.agent_settings.append(agent_setting)

    def add_team(self, agent_brains: Union[list, tuple], locations: Union[list, tuple], team_name,
                 custom_properties=None, sense_capability=None,
                 customizable_properties=None, is_traversable=None,
                 visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_opacity=None):
        """Adds a group of agents as a single team (meaning that their 'team' property all have the given team name).

        All parameters except for the `locations` and `agent_brain` defaults to `None`. Which means that their values
        are obtained from the "scenarios/defaults.json" file under the segment AgentBody.

        Parameters
        ----------
        agent_brains
            The list or tuple of AgentBrain that will control each agent in the team. Should be of the same size as
            `locations`.
        locations
            The list or tuple of locations in the form of [x, y] at which coordinates each agent starts in the team.
            Should be of the same size as `locations`.
        team_name
            The
        custom_properties
            ..
        sense_capability
            ..
        customizable_properties
            ..
        is_traversable
            ..
        visualize_size
            ..
        visualize_shape
            ..
        visualize_colour
            ..
        visualize_opacity
            ..

        Returns
        -------
        None
            ..

        """

        self.add_multiple_agents(agent_brains, locations, custom_properties=custom_properties,
                                 sense_capabilities=sense_capability, customizable_properties=customizable_properties,
                                 is_traversable=is_traversable,
                                 teams=team_name, visualize_sizes=visualize_size, visualize_shapes=visualize_shape,
                                 visualize_colours=visualize_colour, visualize_opacities=visualize_opacity)

    def add_multiple_agents(self, agents, locations, custom_properties=None,
                            sense_capabilities=None, customizable_properties=None,
                            is_traversable=None,
                            teams=None, visualize_sizes=None, visualize_shapes=None,
                            visualize_colours=None, visualize_opacities=None, visualize_depths=None):
        """

        Parameters
        ----------
        agents
        locations
        custom_properties
        sense_capabilities
        customizable_properties
        is_traversable
        teams
        visualize_sizes
        visualize_shapes
        visualize_colours
        visualize_opacities
        visualize_depths

        Returns
        -------

        """

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
                           visualize_size=visualize_sizes[idx],
                           visualize_shape=visualize_shapes[idx],
                           visualize_colour=visualize_colours[idx],
                           visualize_depth=visualize_depths[idx],
                           visualize_opacity=visualize_opacities[idx],
                           **custom_properties[idx])



    def add_agent_prospect(self, location, agent, probability, name="Agent", customizable_properties=None,
                           sense_capability=None,
                           is_traversable=None, team=None, possible_actions=None,
                           is_movable=None,
                           visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_opacity=None,
                           visualize_depth=None, **custom_properties):

        # Add agent as normal
        self.add_agent(location, agent, name, customizable_properties, sense_capability,
                       is_traversable, team, possible_actions, is_movable,
                       visualize_size, visualize_shape, visualize_colour, visualize_depth,
                       visualize_opacity, **custom_properties)

        # Get the last settings (which we just added) and add the probability
        self.agent_settings[-1]['probability'] = probability

    def add_object(self, location, name, callable_class=None, customizable_properties=None,
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

    def add_object_prospect(self, location, name, probability, callable_class=None, customizable_properties=None,
                            is_traversable=None,
                            visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_depth=None,
                            visualize_opacity=None, **custom_properties):
        # Add object as normal
        self.add_object(location, name, callable_class, customizable_properties,
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
        if is_movable is None:
            is_movable = [None for _ in range(len(locations))]
        elif isinstance(is_movable, bool):
            is_movable = [is_movable for _ in range(len(locations))]

        if callable_classes is None:
            callable_classes = [EnvObject for _ in range(len(locations))]
        elif isinstance(callable_classes, Callable):
            callable_classes = [callable_classes for _ in range(len(locations))]

        if names is None:
            names = [callable_class.__name__ for callable_class in callable_classes]
        elif isinstance(names, str):
            names = [names for _ in range(len(locations))]

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
            self.add_object(location=locations[idx], name=names[idx], callable_class=callable_classes[idx],
                            customizable_properties=customizable_properties[idx],
                            is_traversable=is_traversable[idx], is_movable=is_movable[idx],
                            visualize_size=visualize_sizes[idx], visualize_shape=visualize_shapes[idx],
                            visualize_colour=visualize_colours[idx], visualize_depth=visualize_depths[idx],
                            visualize_opacity=visualize_opacities[idx], **custom_properties[idx])

    def add_human_agent(self, location, agent, name="HumanAgent", customizable_properties=None, sense_capability=None,
                        is_traversable=None, team=None, possible_actions=None,
                        is_movable=None,
                        visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_depth=None,
                        visualize_opacity=None, key_action_map=None, **custom_properties):

        # Check if location and agent are of correct type
        assert isinstance(location, list) or isinstance(location, tuple)
        assert isinstance(agent, HumanAgentBrain)

        for existingAgent in self.agent_settings:
            if existingAgent["mandatory_properties"]["name"] == name:
                raise Exception(f"A human agent with the name {name} was already added. Agent names should be unique.",
                                name)
        # Load the defaults for any variable that is not defined
        # Obtain any defaults from the defaults.json file if not set already.
        if is_traversable is None:
            is_traversable = get_default_value(class_name="AgentBody", property_name="is_traversable")
        if visualize_size is None:
            visualize_size = get_default_value(class_name="AgentBody", property_name="visualize_size")
        if visualize_shape is None:
            visualize_shape = get_default_value(class_name="AgentBody", property_name="visualize_shape")
        if visualize_colour is None:
            visualize_colour = get_default_value(class_name="AgentBody", property_name="visualize_colour")
        if visualize_opacity is None:
            visualize_opacity = get_default_value(class_name="AgentBody", property_name="visualize_opacity")
        if visualize_depth is None:
            visualize_depth = get_default_value(class_name="AgentBody", property_name="visualize_depth")
        if possible_actions is None:
            possible_actions = get_default_value(class_name="AgentBody", property_name="possible_actions")
        if is_movable is None:
            is_movable = get_default_value(class_name="AgentBody", property_name="is_movable")

        # If default variables are not given, assign them (most empty, except of sense_capability that defaults to all
        # objects with infinite range).
        if custom_properties is None:
            custom_properties = {}
        if sense_capability is None:
            sense_capability = create_sense_capability([], [])  # Create sense capability that perceives all
        if customizable_properties is None:
            customizable_properties = []

        # Check if the agent is of HumanAgent, if not; use the add_agent method
        inh_path = get_inheritence_path(agent.__class__)
        if 'HumanAgent' not in inh_path:
            Exception(f"You are adding an agent that does not inherit from HumanAgent with the name {name}. Use "
                      f"factory.add_agent to add autonomous agents.")

        # Append the user input map to the custom properties
        custom_properties["key_action_map"] = key_action_map

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

        # Get all locations in the rectangle
        min_x = top_left_location[0]
        max_x = top_left_location[0] + width
        min_y = top_left_location[1]
        max_y = top_left_location[1] + height

        noise_grid = utils._white_noise(min_x, max_x, min_y, max_y, rng=self.rng)

        for x in range(noise_grid.shape[0]):
            for y in range(noise_grid.shape[1]):
                # get noise point
                noise = noise_grid[x, y]

                # convert from [-1,1] range to [0,1] range, and flip
                opacity = 1 - ((noise + 1.0) / 2.0)
                opacity = np.clip(opacity * smoke_thickness_multiplier, 0, 1)

                # add the smokeTile
                self.add_object(location=[x, y], name=name, callable_class=SmokeTile,
                                visualize_colour=visualize_colour, visualize_opacity=opacity,
                                visualize_depth=visualize_depth, **custom_properties)

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
                                  visualize_opacities=visualize_opacity, visualize_depths=visualize_depth,
                                  is_movable=is_movable)

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
        door_locations = [] if door_locations is None else door_locations
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
            self.add_object(location=door_loc, name=f"{name} - door@{door_loc}", callable_class=Door,
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
            world._register_env_object(env_object)

        # Register all agents (including checks)
        for agent, agent_avatar in avatars:
            world._register_agent(agent, agent_avatar)

        # Register all teams and who is in them
        world._register_teams()

        # Add all loggers if any
        for logger_class, arguments in self.loggers:
            logger = logger_class(**arguments)
            logger._set_world_nr(self.worlds_created)
            world._register_logger(logger)



        # Return the (successful/stable) world
        return world

    def __create_grid_world(self):
        args = self.world_settings
        # create a world ID in the shape of "world_" + world number + seeded random int
        args['world_ID'] = f"world_{self.worlds_created}"
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
            argspecs = inspect.getfullargspec(callable_class)
            args = argspecs.args  # does not give *args or **kwargs names
            defaults = argspecs.defaults  # defaults (if any) of the last n elements in args
            varkw = argspecs.varkw # **kwargs names

            argspecsv2 = inspect.getfullargspec(callable_class)

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
            kwargs = [prop_name for prop_name in custom_props.keys() if prop_name not in args.keys()]
            if varkw is None and len(kwargs) > 0:
                warnings.warn(f"The following properties are not used in the creation of environment object of type "
                              f"{callable_class.__name__} with name {mandatory_props['name']}; {kwargs}, because "
                              f"the class does nto have a **kwargs argument in the constructor.")

            # if a **kwargs argument was defined in the object constructor, pass all custom properties to the object
            elif varkw is not None and len(kwargs) > 0:
                for arg in kwargs:
                    args[arg] = custom_props[arg]


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
                'isAgent': True,
                'sense_capability': sense_capability,
                'class_callable': agent.__class__,
                'callback_agent_get_action': agent._get_action,
                'callback_agent_set_action_result': agent._set_action_result,
                'callback_agent_observe': agent.filter_observations,
                'callback_agent_log': agent._get_log_data,
                'callback_agent_get_messages': agent._get_messages,
                'callback_agent_set_messages': agent._set_messages,
                'callback_agent_initialize': agent.initialize,
                'customizable_properties': customizable_props,
                **custom_props}

        # Parse arguments and create the AgentAvatar
        args = self.__instantiate_random_properties(args)
        avatar = AgentBody(**args)

        # We return the agent and avatar (as we will complete the initialisation of the agent when we register it)
        return agent, avatar

    def __instantiate_random_properties(self, args):
        # Checks if all given arguments in the dictionary are not None, and if they are of RandomProperty or
        # RandomLocation, their (random) value is retrieved.
        for k, v in args.items():
            if isinstance(v, RandomProperty):
                args[k] = v._get_property(self.rng)

        return args

    def __reset_random(self):
        # TODO resets all RandomProperty and RandomLocation, is called after creating a world so all duplicates can be
        # TODO selected again.
        pass


    def startup(self):
        """ Start any world-overarching MATRXS scripts, such as, if requested, the API or MATRXS visualization.
        Returns
        -------
        """
        if self.run_matrxs_api:
            self.api_info["api_thread"] = api.run_api(self.verbose)

        if self.run_matrxs_visualizer:
            self.matrxs_visualizer_thread = visualization_server.run_matrxs_visualizer(self.verbose)

    def stop(self):
        """ Stop any world-overarching MATRXS scripts, such as, if started, the API or MATRXS visualization.
        Returns
        -------
        """
        if self.run_matrxs_api:
            print("Shutting down MATRXs API")
            r = requests.get("http://localhost:" + str(api.port) + "/shutdown_API")
            self.api_info["api_thread"].join()

        if self.run_matrxs_visualizer:
            print("Shutting down MATRXs visualizer")
            r = requests.get("http://localhost:" + str(visualization_server.port) + "/shutdown_visualizer")
            self.matrxs_visualizer_thread.join()




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

    def _get_property(self, rng: RandomState, size=None):
        vals = self.values.copy()
        if not self.allow_duplicates:
            for it in self.selected_values:
                vals.remove(it)
        choice = rng.choice(vals, p=self.distribution, size=size, replace=self.allow_duplicates)
        self.selected_values.add(choice)
        return choice

    def reset(self):
        self.selected_values = set()
