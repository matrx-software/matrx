import inspect
import itertools
import warnings
from collections import OrderedDict
from typing import Callable, Union, Iterable
import requests

from numpy.random.mtrand import RandomState
import numpy as np

from matrx.agents.agent_brain import AgentBrain
from matrx.agents.capabilities.capability import SenseCapability
from matrx.agents.agent_types.human_agent import HumanAgentBrain
from matrx.grid_world import GridWorld
from matrx.logger.logger import GridWorldLogger
from matrx.objects.agent_body import AgentBody
from matrx.objects.env_object import EnvObject, _get_inheritence_path
from matrx import utils
from matrx.agents.capabilities.capability import create_sense_capability
from matrx.objects.standard_objects import Wall, Door, AreaTile, SmokeTile
from matrx.goals.goals import LimitedTimeGoal, WorldGoal

import matrx.defaults as defaults

# addons
from matrx.api import api
from matrx_visualizer import visualization_server


class WorldBuilder:
    """ Used to create one or more worlds according to a singel blueprint.
    """

    def __init__(self, shape, tick_duration=0.5, random_seed=1,
                 simulation_goal=1000, run_matrx_api=True,
                 run_matrx_visualizer=False, visualization_bg_clr="#C2C2C2",
                 visualization_bg_img=None, verbose=False):

        """
        With the constructor you can set a number of general properties and
        from the resulting instance you can call numerous methods to add new
        objects and/or agents.

        Parameters
        ----------
        shape : tuple or list
            Denotes the width and height of the world you create.

        tick_duration : float (optional, default 0.5)
            The duration of a single 'tick' or loop in the game-loop of the
            world you create.

        random_seed : int, (optional, default 1)
            The master random seed on which all objects, agents and worlds are
            seeded. Should be a positive non-zero integer.

        simulation_goal : WorldGoal, int, list or list (optional, default 1000)
            The goal or goals of the world, either a single `WorldGoal`, a
            list of such or a positive non-zero integer to denote the maximum
            number of 'ticks' the world(s) has to run.

        run_matrx_api : bool (optional, default True)
            Whether to run the API. This API is used to connect the default
            MATRX visualizer or a custom one.

        run_matrx_visualizer : bool (optional, default False)
            Whether to run the default MATRX visualizer, this requires the API
            to be run. When set to True, it starts the visualization that is
            accessible through http://localhost:3000.

        visualization_bg_clr : string (optional, "C2C2C2")
            The color of the world when visualized using MATRX' own
            visualisation server. A string representation of hexadecimal color.

        visualization_bg_img : string (optional, None)
            An optional background image of the world when visualized using
            MATRX' own visualisation server. A string of the path to the image
            file. When None, no background image is used.

        verbose : bool (optional, False)
            Whether the subsequent created world should be verbose or not.

        Raises
        ------
        ValueError
            On an incorrect argument. The exception specifies further what
            argument and what is erroneous about it.

        Examples
        --------

        This creates a WorldBuilder that creates world of a certain size (here
        10 by 10);

            >>> from matrx.world_builder import WorldBuilder
            >>> builder = WorldBuilder(shape=(10, 10))

        To create a WorldBuilder with a black background, a tick duration as
        fast as possible and with a different master random seed;

            >>> from matrx.world_builder import WorldBuilder
            >>> builder = WorldBuilder(shape=(10, 10), random_seed=42, \
            >>>    tick_duration=-1, visualization_bg_clr="#000000")

        """

        # Check if shape is of correct type and length
        if not isinstance(shape, list) and not isinstance(shape, tuple) \
                and len(shape) != 2:
            raise ValueError(f"The given grid shape {shape} is not of type "
                             f"List, Tuple or of size two.")

        # convert int to float
        if isinstance(tick_duration, int):
            tick_duration = float(tick_duration)

        # Check that tick duration is of float and a positive number.
        if not isinstance(tick_duration, float) and tick_duration >= 0.0:
            raise ValueError(f"The given tick_duration {tick_duration} should "
                             f"be a Float and larger or equal than 0.0.")

        # Check that the random seed is a positive non-zero integer
        if not isinstance(random_seed, int) and random_seed > 0:
            raise ValueError(f"The given random_seed {random_seed} should be "
                             f"an Int and bigger or equal to 1.")

        # Check if the simulation_goal is a SimulationGoal, an int or a list
        # or tuple of SimulationGoal
        if not isinstance(simulation_goal, WorldGoal) and \
                not isinstance(simulation_goal, int) \
                and not (isinstance(simulation_goal, Iterable)
                         and (sum(1 for _ in simulation_goal)) > 0):
            raise ValueError(f"The given simulation_goal {simulation_goal} "
                             f"should be of type {WorldGoal.__name__} or a "
                             f"list/tuple of {WorldGoal.__name__}, or it "
                             f"should be an int denoting the max" f"number of "
                             f"ticks the world should run (negative for "
                             f"infinite).")

        # Check the background color
        if not isinstance(visualization_bg_clr, str) and \
                len(visualization_bg_clr) != 7 and \
                visualization_bg_clr[0] != "#":
            raise ValueError(f"The given visualization_bg_clr "
                             f"{visualization_bg_clr} should be a Str of "
                             f"length 7 with an initial '#'' (a hexidecimal "
                             f"color string).")

        # Check if the background image is a path
        if visualization_bg_img is not None \
                and not isinstance(visualization_bg_img, str):
            raise ValueError(
                f"The given visualization_bg_img {visualization_bg_img} "
                f"should be of type str denoting a path to an image.")

        if not isinstance(run_matrx_visualizer, bool):
            raise ValueError(f"The given value {run_matrx_visualizer} for run_"
                             f"matrx_visualizer is invalid, should be of type "
                             f"bool ")

        if not isinstance(run_matrx_api, bool):
            raise ValueError(f"The given value {run_matrx_api} for run_matrx_"
                             f"api is invalid, should be of type bool.")

        if not run_matrx_api and run_matrx_visualizer:
            raise ValueError(f"Run_matrx_api is set to False while "
                             f"run_matrx_visualizer is set to True. The MATRX "
                             f"visualizer requires the api to work, so this "
                             f"is not possible.")

        # Set our random number generator
        self.rng = np.random.RandomState(random_seed)
        # Set our settings place holders
        self.agent_settings = []
        self.object_settings = []
        # Set our logger place holders
        self.loggers = []

        # initialize an api variables
        self.run_matrx_api = run_matrx_api
        self.api_info = {"run_matrx_api": run_matrx_api,
                         "api_thread": False}

        # initialize the visualization variables
        self.run_matrx_visualizer = run_matrx_visualizer
        self.matrx_visualizer_thread = False

        # Whether the world factory and evrything else should print stuff
        self.verbose = verbose

        # If simulation goal is an integer, we create a LimitedTimeGoal with
        # that number of ticks
        if isinstance(simulation_goal, int):
            simulation_goal = LimitedTimeGoal(max_nr_ticks=simulation_goal)

        # Set our world settings
        self.world_settings = \
            self.__set_world_settings(shape=shape, tick_duration=tick_duration,
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
        # use the default (print all warnings once per location [module and
        # line number])
        else:
            warnings.simplefilter("default")

    def worlds(self, nr_of_worlds: int = 100):
        """ A Generator of worlds.

        Parameters
        ----------
        nr_of_worlds: int (default, 100)
            The number of worlds that should be generated.

        Yields
        ------
        GridWorld
            A GridWorld, where all random properties and prospects are
            sampled using the given master seed.

        Raises
        ------
        ValueError
            When `nr_of_worlds` is not an integer. zero or negative.

        See Also
        --------
        :any:`~matrx.GridWorld.run`:
            Start a GridWorld instance.

        Examples
        --------

        Create a world builder and generate 10 worlds and run them:
        >>> from matrx.world_builder import WorldBuilder
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> for w in builder.worlds(): w.run()


        """

        if not isinstance(nr_of_worlds, int) and nr_of_worlds <= 0:
            raise ValueError(f"The given nr_of_worlds {nr_of_worlds} should "
                             f"be of type Int and larger or equal to 1.")

        while self.worlds_created < nr_of_worlds:
            yield self.get_world()

    def get_world(self):
        """ Create a single world using the blueprint of this builder.

        The returned GridWorld can be started with `world.run()`.

        Returns
        -------
        world: GridWorld
            A GridWorld instance representing the create world using this
            builder.

        See Also
        --------
        :any:`~matrx.GridWorld.run`:
            Start a GridWorld instance.
        """
        # TODO Refer to GridWorld.run()
        self.worlds_created += 1
        world = self.__create_world()
        self.__reset_random()
        return world

    def add_logger(self, logger_class, log_strategy=None, save_path=None,
                   file_name=None, file_extension=None, delimiter=None,
                   **kwargs):
        """ Adds a data logger to the world's blueprint.

        Parameters
        ----------
        logger_class: Logger
            The class of Logger you wish to add.

        log_strategy: int, str (default, None)
            The logging strategy used. Supports either an integer denoting the
            number of ticks the logger should be called. Or either one of the
            following:

            * GridWorldLogger.LOG_ON_LAST_TICK: Log only on last tick.

            * GridWorldLogger.LOG_ON_FIRST_TICK: Log only on first tick.

            * GridWorldLogger.LOG_ON_GOAL_REACHED: Log whenever a goal is
            reached.

        save_path: string (default, None)
            A path to a folder where to save the data. When set to None, a
            folder "logs" is created and used.

        file_name: string (default, None)
            The file name of the stored data. When set to None, a name of
            "_<time_stamp>" will be used. With <time_stamp> the time of world
            creation.

        file_extension: string (default, None)
            The extension of the file. When set to None, ".csv" is used.

        delimiter: string (default, None)
            The delimiter of the columns in the data file. When set to None,
            the ";" is used.

        **kwargs
            Any key word arguments the given `logger_class` requires.

        Raises
        ------
        ValueError
            When the given `logger_class` is not of (super) type
            `GridWorldLogger`.

        See Also
        --------
        :any:`~matrx.logger.GridWorldLogger`:
            The interface class to which the passed `logger_class` should
            from. inherit
        :any:`~matrx.logger`:
            The module with predefined loggers for you to use.

        Examples
        --------

        Add a logger that logs all agent actions every tick:
        >>> from matrx import WorldBuilder
        >>> from matrx.logger import LogActions
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> builder.add_logger(LogActions)

        Add a logger that logs when agents are idle or not every time a goal
        will be achieved:
        >>> from matrx import WorldBuilder
        >>> from matrx.logger import LogIdleAgents, GridWorldLogger
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> builder.add_logger(LogIdleAgents, \
        >>>     log_strategy=GridWorldLogger.LOG_ON_GOAL_REACHED)

        """

        if issubclass(logger_class, GridWorldLogger):

            set_params = {'log_strategy': log_strategy, 'save_path': save_path,
                          'file_name': file_name,
                          'file_extension': file_extension,
                          'delimiter': delimiter}

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
            raise ValueError(f"The logger is not of type, nor inherits from, "
                             f"{GridWorldLogger.__name__}.")

    def add_agent(self, location: Union[tuple, list], agent_brain: AgentBrain,
                  name, customizable_properties: Union[tuple, list] = None,
                  sense_capability: SenseCapability = None,
                  is_traversable: bool = True, team: str = None,
                  possible_actions: list = None, is_movable: bool = None,
                  visualize_size: float = None,
                  visualize_shape: Union[float, str] = None,
                  visualize_colour: str = None, visualize_depth: int = None,
                  visualize_opacity: float = None,
                  visualize_when_busy: bool = None, **custom_properties):
        """ Adds a single agent to the world's blueprint.

        This methods adds an agent body to every created world at the specified
        location and linked to an instance of the provided agent brain.

        All keyword parameters default to None. Which means that their values
        are obtained from their similar named constants in `matrx.defaults`.

        Parameters
        ----------
        location: tuple or list
            The location (x,y) of the to be added agent.

        agent_brain: AgentBrain
            The AgentBrain instance that will control the agent.

        name: string
            The name of the agent, should be unique to allow the visualisation
            to have a single web page per agent. If the name is already used,
            an exception is thrown.

        customizable_properties: list (optional, None)
            A list or tuple of names of properties for this agent that can be
            altered or customized. Either by the agent itself or by other
            agents or objects. If a property value gets changed that is not
            in this list than an exception is thrown.

        sense_capability: SenseCapability (optional, None)
            The SenseCapability object belonging this this agent's AgentBody.
            Used by the GridWorld to pre-filter objects and agents from this
            agent's states when querying for actions. Defaults to a
            SenseCapability that sees all object types within the entire world.

        is_traversable: bool (optional, None)
            Denotes whether other agents and object can move over this agent.
            It also throws an exception when this is set to False and another
            object/agent with this set to False is added to the same location.

        team: string (optional, None)
            The team name. Used to group agents together. Defaults to this
            agent's name + "_team" to signify it forms its own team.

        possible_actions: list (optional, None)
            A list or tuple of the names of the Action classes this agent can
            perform. With this you can limit the actions this agent can
            perform.

        is_movable: bool (optional, None)
            Whether this agent can be moved by other agents (currently this
            only happens with the DropObjectAction and PickUpAction).

        visualize_size: float (optional, None)
            The size of this agent in its visualisation. A value of 1.0
            denotes the full grid location square, whereas a value of 0.5
            denotes half, and 0.0 an infinitesimal small size.

        visualize_shape: int or string (optional, None)
            The shape of this agent in its visualisation. Depending on the
            value it obtains this shape:

            * 0 = a square

            * 1 = a triangle

            * 2 = a circle

            * Path to image or GIF = that image scaled to match the size.

        visualize_colour: string (optional, None)
            The colour of this agent in its visualisation. Should be a string
            hexadecimal colour value.

        visualize_depth: int (optional, None)
            The visualisation depth of this agent in its visualisation. It
            denotes the 'layer' on which it is visualized. A larger value is
            more on 'top'.

        visualize_opacity: float (optional, None)
            The opacity of this agent in its visualization. A value of 1.0
            means full opacity and 0.0 no opacity.

        visualize_when_busy: bool (optional, None)
            Whether to visualize when an agent is busy with a action. True
            means show this using a loading icon, false means do not show
            this in the visualizer.

        custom_properties: list (optional, None)
            Any additional given keyword arguments will be encapsulated in
            this dictionary. These will be added to the AgentBody as
            custom_properties which can be perceived by other agents and
            objects or which can be used or altered (if allowed to by the
            customizable_properties list) by the AgentBrain or others.

        Raises
        ------
        ValueError
            When the given agent name is already added to this WorldFactory
            instance.

        Examples
        --------

        Add a simple patrolling agent that patrols the world.
        >>> from matrx import WorldBuilder
        >>> from matrx.logger import LogActions
        >>> from matrx.agents import PatrollingAgentBrain
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> waypoints = [(0, 0), (10, 0), (10, 10), (0, 10)]
        >>> brain = PatrollingAgentBrain(waypoints)
        >>> builder.add_agent((5, 5), brain, name="Patroller")

        Add an agent with some custom property `foo="bar"` and w.
        >>> from matrx import WorldBuilder
        >>> from matrx.logger import LogActions
        >>> from matrx.agents import AgentBrain
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> brain = AgentBrain()
        >>> builder.add_agent((5, 5), brain, name="Agent", foo="bar")

        """

        # Check if location and agent are of correct type
        if not isinstance(location, list) \
                and not isinstance(location, tuple) \
                and len(location) != 2:
            raise ValueError(f"The given location {location} while adding the "
                             f"agent with name {name} is not a list, tuple or "
                             f"of length two.")

        if not isinstance(agent_brain, AgentBrain):
            raise ValueError(f"The given agent_brain while adding agent with "
                             f"name {name} is not of type "
                             f"{AgentBrain.__name__} but of type"
                             f" {agent_brain.__class__.__name__}.")

        # Check if the agent name is unique
        for existingAgent in self.agent_settings:
            if existingAgent["mandatory_properties"]["name"] == name:
                raise ValueError(f"An agent with the name {name} was already "
                                 f"added. Agent names should be unique.",
                                 name)

        # Load the defaults for any variable that is not defined
        # Obtain any defaults from the defaults.py file if not set already.
        if is_traversable is None:
            is_traversable = defaults.AGENTBODY_IS_TRAVERSABLE
        if visualize_size is None:
            visualize_size = defaults.AGENTBODY_VIS_SIZE
        if visualize_shape is None:
            visualize_shape = defaults.AGENTBODY_VIS_SHAPE
        if visualize_colour is None:
            visualize_colour = defaults.AGENTBODY_VIS_COLOUR
        if visualize_opacity is None:
            visualize_opacity = defaults.AGENTBODY_VIS_OPACITY
        if visualize_when_busy is None:
            visualize_when_busy = defaults.AGENTBODY_VIS_BUSY
        if visualize_depth is None:
            visualize_depth = defaults.AGENTBODY_VIS_DEPTH
        if possible_actions is None:
            possible_actions = defaults.AGENTBODY_POSSIBLE_ACTIONS
        if is_movable is None:
            is_movable = defaults.AGENTBODY_IS_MOVABLE

        # If default variables are not given, assign them (most empty, except
        # of sense_capability that defaults to all objects with infinite
        # range).
        if custom_properties is None:
            custom_properties = {}
        if sense_capability is None:
            # Create sense capability that perceives all
            sense_capability = create_sense_capability([], [])
        if customizable_properties is None:
            customizable_properties = []

        # Check if the agent is not of HumanAgent, if so; use the add_human_
        # agent method
        inh_path = _get_inheritence_path(agent_brain.__class__)
        if 'HumanAgent' in inh_path:
            ValueError(f"You are adding an agent that is or inherits from "
                       f"HumanAgent with the name {name}. Use "
                       f"factory.add_human_agent to add such agents.")

        # Define a settings dictionary with all we need to register and add
        # an agent to the GridWorld
        agent_setting = {"agent": agent_brain,
                         "custom_properties": custom_properties,
                         "customizable_properties": customizable_properties,
                         "sense_capability": sense_capability,
                         "mandatory_properties": {
                             "name": name,
                             "is_movable": is_movable,
                             "is_traversable": is_traversable,
                             "possible_actions": possible_actions,
                             # is you want a human agent, use
                             # factory.add_human_agent()
                             "is_human_agent": False,
                             "visualize_size": visualize_size,
                             "visualize_shape": visualize_shape,
                             "visualize_colour": visualize_colour,
                             "visualize_opacity": visualize_opacity,
                             "visualize_depth": visualize_depth,
                             "visualize_when_busy": visualize_when_busy,
                             "location": location,
                             "team": team}
                         }

        self.agent_settings.append(agent_setting)

    def add_team(self, agent_brains: Union[list, tuple],
                 locations: Union[list, tuple], team_name,
                 custom_properties=None, sense_capability=None,
                 customizable_properties=None, is_traversable=None,
                 visualize_size=None, visualize_shape=None,
                 visualize_colour=None, visualize_opacity=None,
                 visualize_when_busy=None):
        """ Adds multiple agents as a single team.

        All parameters except for the `locations` and `agent_brain` default to
        `None`. Which means that their values are obtained from the
        `matrx.defaults`.

        Parameters
        ----------
        agent_brains: list or tuple
            The list or tuple of AgentBrain that will control each agent in
            the team. Should be of the same size as `locations`.

        locations: list or tuple
            The list or tuple of locations in the form of (x, y) at which
            coordinates each agent starts in the team. Should be of the same
            size as `locations`.

        team_name: string
            The name of the team these agents are part of.

        custom_properties: list (optional, None)

        sense_capability: SenseCapability or list (optional, None)
            A single `SenseCapability` used for every agent, or a list of those
            for every given agent.

        customizable_properties: list (optional, None)
            A list of property names that each agent can edit. When it is a
            list of listed properties, it denotes a unique set of customizable
            properties for every agent.

        is_traversable: bool or list (optional, None)
            A list of booleans or a single boolean denoting either for each
            agent or all agents their traversability.

        visualize_size: float or list (optional, None)
            A list of floats or a single float denoting either for each
            agent or all agents their traversability. A value of 0.0 means no
            size, and a value of 1.0 fills the entire tile.

        visualize_shape: int, string or list (optional, None)
            The shape of the agents in the visualisation. When a list, denotes
            the shape of every agent. Depending on the value it obtains this
            shape:

            * 0 = a square

            * 1 = a triangle

            * 2 = a circle

            * Path to image or GIF = that image scaled to match the size.

        visualize_colour: string or list (optional, None)
            The colour of this agent in its visualisation. Should be a string
            hexadecimal colour value.

        visualize_opacity: float or list (optional, None)
            The opacities of the agents in the visualization. A value of 1.0
            means full opacity and 0.0 no opacity.

        visualize_when_busy: bool or list (optional, None)
            Whether to visualize when an agent is busy with a action. True
            means show this using a loading icon, false means do not show
            this in the visualizer.

        visualize_when_busy
            Whether to visualize a loading icon when the agent is busy with an
            action.

        Raises
        ------


        """

        self.add_multiple_agents(agent_brains, locations, custom_properties=custom_properties,
                                 sense_capabilities=sense_capability, customizable_properties=customizable_properties,
                                 is_traversable=is_traversable,
                                 teams=team_name, visualize_sizes=visualize_size, visualize_shapes=visualize_shape,
                                 visualize_colours=visualize_colour, visualize_opacities=visualize_opacity,
                                 visualize_when_busy=visualize_when_busy)

    def add_multiple_agents(self, agents, locations, custom_properties=None,
                            sense_capabilities=None, customizable_properties=None,
                            is_traversable=None,
                            teams=None, visualize_sizes=None, visualize_shapes=None,
                            visualize_colours=None, visualize_opacities=None, visualize_depths=None,
                            visualize_when_busy=None):
        """ Add agents in bulk

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
        visualize_when_busy

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

        if visualize_when_busy is None:
            visualize_when_busy = [None for _ in range(len(agents))]
        elif isinstance(visualize_when_busy, bool):
            visualize_when_busy = [visualize_when_busy for _ in range(len(agents))]

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
                           visualize_when_busy=visualize_when_busy[idx],
                           **custom_properties[idx])

    def add_agent_prospect(self, location, agent, probability, name="Agent", customizable_properties=None,
                           sense_capability=None,
                           is_traversable=None, team=None, possible_actions=None,
                           is_movable=None,
                           visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_opacity=None,
                           visualize_depth=None, visualize_when_busy=None, **custom_properties):

        # Add agent as normal
        self.add_agent(location, agent, name, customizable_properties, sense_capability,
                       is_traversable, team, possible_actions, is_movable,
                       visualize_size, visualize_shape, visualize_colour, visualize_depth,
                       visualize_opacity, visualize_when_busy, **custom_properties)

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

        # Check if location only contains integers, otherwise warn use and cast to int
        if not (isinstance(location[0], int) and isinstance(location[1], int)):
            warnings.warn(f"The location {location} of {name} should contain only integers, "
                          f"encountered {str(type(location[0]))} and {str(type(location[1]))} . "
                          f"Casting these to integers resulting in "
                          f"{(int(location[0]), int(location[1]))}")
            location = (int(location[0]), int(location[1]))

        # Load default parameters if not passed
        if is_movable is None:
            is_movable = defaults.ENVOBJECT_IS_MOVABLE

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
                            is_traversable=None, is_movable=None,
                            visualize_size=None, visualize_shape=None, visualize_colour=None, visualize_depth=None,
                            visualize_opacity=None, **custom_properties):
        # Add object as normal
        self.add_object(location, name, callable_class, customizable_properties,
                        is_traversable, is_movable,
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
        elif isinstance(names, str) or isinstance(names, RandomProperty):
            names = [names for _ in range(len(locations))]

        if customizable_properties is None:
            customizable_properties = [None for _ in range(len(locations))]
        elif not any(isinstance(el, list) for el in customizable_properties):
            customizable_properties = [customizable_properties for _ in range(len(locations))]

        if is_traversable is None:
            is_traversable = [None for _ in range(len(locations))]
        elif isinstance(is_traversable, bool) or isinstance(is_traversable, RandomProperty):
            is_traversable = [is_traversable for _ in range(len(locations))]

        if visualize_sizes is None:
            visualize_sizes = [None for _ in range(len(locations))]
        elif isinstance(visualize_sizes, int) or isinstance(visualize_sizes, RandomProperty):
            visualize_sizes = [visualize_sizes for _ in range(len(locations))]

        if visualize_shapes is None:
            visualize_shapes = [None for _ in range(len(locations))]
        elif isinstance(visualize_shapes, int) or isinstance(visualize_shapes, RandomProperty):
            visualize_shapes = [visualize_shapes for _ in range(len(locations))]

        if visualize_colours is None:
            visualize_colours = [None for _ in range(len(locations))]
        elif isinstance(visualize_colours, str) or isinstance(visualize_colours, RandomProperty):
            visualize_colours = [visualize_colours for _ in range(len(locations))]

        if visualize_opacities is None:
            visualize_opacities = [None for _ in range(len(locations))]
        elif isinstance(visualize_opacities, float) or isinstance(visualize_opacities, RandomProperty):
            visualize_opacities = [visualize_opacities for _ in range(len(locations))]

        if visualize_depths is None:
            visualize_depths = [None for _ in range(len(locations))]
        elif isinstance(visualize_depths, str) or isinstance(visualize_depths, RandomProperty):
            visualize_depths = [visualize_depths for _ in range(len(locations))]

        if custom_properties is None:
            custom_properties = [{} for _ in range(len(locations))]
        elif isinstance(custom_properties, dict):
            custom_properties = [custom_properties for _ in range(len(locations))]

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
                        visualize_opacity=None, visualize_when_busy=None, key_action_map=None, **custom_properties):

        # Check if location and agent are of correct type
        assert isinstance(location, list) or isinstance(location, tuple)
        assert isinstance(agent, HumanAgentBrain)

        for existingAgent in self.agent_settings:
            if existingAgent["mandatory_properties"]["name"] == name:
                raise Exception(f"A human agent with the name {name} was already added. Agent names should be unique.",
                                name)
        # Load the defaults for any variable that is not defined
        # Obtain any defaults from the defaults.py file if not set already.
        if is_traversable is None:
            is_traversable = defaults.AGENTBODY_IS_TRAVERSABLE
        if visualize_size is None:
            visualize_size = defaults.AGENTBODY_VIS_SIZE
        if visualize_shape is None:
            visualize_shape = defaults.AGENTBODY_VIS_SHAPE
        if visualize_colour is None:
            visualize_colour = defaults.AGENTBODY_VIS_COLOUR
        if visualize_opacity is None:
            visualize_opacity = defaults.AGENTBODY_VIS_OPACITY
        if visualize_depth is None:
            visualize_depth = defaults.AGENTBODY_VIS_DEPTH
        if visualize_when_busy is None:
            visualize_when_busy = defaults.AGENTBODY_VIS_BUSY
        if possible_actions is None:
            possible_actions = defaults.AGENTBODY_POSSIBLE_ACTIONS
        if is_movable is None:
            is_movable = defaults.AGENTBODY_IS_MOVABLE

        # If default variables are not given, assign them (most empty, except of sense_capability that defaults to all
        # objects with infinite range).
        if custom_properties is None:
            custom_properties = {}
        if sense_capability is None:
            sense_capability = create_sense_capability([], [])  # Create sense capability that perceives all
        if customizable_properties is None:
            customizable_properties = []

        # Check if the agent is of HumanAgent, if not; use the add_agent method
        inh_path = _get_inheritence_path(agent.__class__)
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
                             "visualize_when_busy": visualize_when_busy,
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
        self.add_multiple_objects(locations=locs, callable_classes=AreaTile, names=name,
                                  customizable_properties=customizable_properties, visualize_colours=visualize_colour,
                                  visualize_opacities=visualize_opacity, custom_properties=custom_properties)

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

        noise_grid = _white_noise(min_x, max_x, min_y, max_y, rng=self.rng)

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
                 doors_open=False, wall_visualize_colour=None, wall_visualize_opacity=None,
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
        width = int(width) - 1
        height = int(height) - 1

        # Set corner coordinates
        top_left = (int(top_left_location[0]), int(top_left_location[1]))
        top_right = (int(top_left_location[0]) + int(width), int(top_left_location[1]))
        bottom_left = (int(top_left_location[0]), int(top_left_location[1]) + int(height))
        bottom_right = (int(top_left_location[0]) + int(width), int(top_left_location[1]) + int(height))

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
                                  visualize_colours=wall_visualize_colour,
                                  visualize_opacities=wall_visualize_opacity,
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

    @staticmethod
    def get_room_locations(room_top_left, room_width, room_height):
        """ Returns the location coordinates within a room.

        This is a helper function for adding objects to a room. It simply returns a list of all (x,y)
        coordinates that fall within the room excluding the walls.

        Parameters
        ----------
        room_top_left: tuple, (x, y)
            The top left coordinates of a room, as used to add that room with methods such as `add_room`.
        room_width: int
            The width of the room.
        room_height: int
            The height of the room.

        Returns
        -------
        list, [(x,y), ...]
            A list of (x, y) coordinates that are encapsulated in the room, excluding walls.

        See Also
        --------
        WorldBuilder.add_room

        """
        xs = list(range(room_top_left[0] + 1, room_top_left[0] + room_width - 1))
        ys = list(range(room_top_left[1] + 1, room_top_left[1] + room_height -1))
        locs = list(itertools.product(xs, ys))
        return locs

    def __set_world_settings(self, shape, tick_duration, simulation_goal, rnd_seed,
                             visualization_bg_clr, visualization_bg_img, verbose):

        if rnd_seed is None:
            rnd_seed = self.rng.randint(0, 1000000)

        # Check if the given shape contains integers, otherwise warn user and cast to int
        if not (isinstance(shape[0], int) and isinstance(shape[1], int)):
            warnings.warn(f"The world's provided shape {shape} should contain integers, "
                          f"encountered {str(type(shape[0]))} and {str(type(shape[1]))} . "
                          f"Casting these to integers resulting in "
                          f"{(int(shape[0]), int(shape[1]))}")
            shape = (int(shape[0]), int(shape[1]))

        world_settings = {"shape": shape,
                          "tick_duration": tick_duration,
                          "simulation_goal": simulation_goal,
                          "rnd_seed": rnd_seed,
                          "visualization_bg_clr": visualization_bg_clr,
                          "visualization_bg_img": visualization_bg_img,
                          "verbose": verbose}

        return world_settings

    def __list_area_locs(self, top_left_location, width, height):
        """
        Provided an area with the top_left_location, width and height,
        generate a list containing all coordinates in that area
        """

        # Get all locations in the rectangle
        xs = list(range(top_left_location[0], top_left_location[0] + width))
        ys = list(range(top_left_location[1], top_left_location[1] + height))
        locs = list(itertools.product(xs, ys))
        return locs

    def __create_world(self):

        # Create the world
        world = self.__create_grid_world()
        # Create all objects first
        objs = []
        for idx, obj_settings in enumerate(self.object_settings):
            # Print progress (so user knows what is going on)
            if idx % max(10, int(len(self.object_settings) * 0.1)) == 0:
                print(f"Creating objects... @{np.round(idx / len(self.object_settings) * 100, 0)}%")

            env_object = self.__create_env_object(obj_settings)
            if env_object is not None:
                objs.append(env_object)

        # Then create all agents
        avatars = []
        for idx, agent_settings in enumerate(self.agent_settings):
            # Print progress (so user knows what is going on)
            if idx % max(10, int(len(self.agent_settings) * 0.1)) == 0:
                print(f"Creating agents... @{np.round(idx / len(self.agent_settings) * 100, 0)}%")

            agent, agent_avatar = self.__create_agent_avatar(agent_settings)
            if agent_avatar is not None:
                avatars.append((agent, agent_avatar))

        # Register all objects (including checks)
        for idx, env_object in enumerate(objs):
            # Print progress (so user knows what is going on)
            if idx % max(10, int(len(objs) * 0.1)) == 0:
                print(f"Adding objects... @{np.round(idx / len(objs) * 100, 0)}%")

            world._register_env_object(env_object)

        # Register all agents (including checks)
        for idx, agent in enumerate(avatars):
            # Print progress (so user knows what is going on)
            if idx % max(10, int(len(objs) * 0.1)) == 0:
                print(f"Adding agents... @{np.round(idx / len(avatars) * 100, 0)}%")
            world._register_agent(agent[0], agent[1])

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
        args['world_id'] = f"world_{self.worlds_created}"
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
                    'is_movable': mandatory_props['is_movable'],
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
            def_args = argspecs.defaults  # defaults (if any) of the last n elements in args
            varkw = argspecs.varkw  # **kwargs names

            # Now assign the default values to kwargs dictionary
            args = OrderedDict({arg: "not_set" for arg in reversed(args[1:])})
            if def_args is not None:
                for idx, default in enumerate(reversed(def_args)):
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
                              f"the class does not have a **kwargs argument in the constructor.")

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

    def startup(self, media_folder=None):
        """ Start any world-overarching MATRX scripts, such as, if requested, the api or MATRX visualization.
        Returns
        -------
        """
        # startup the MATRX API if requested
        if self.run_matrx_api:
            self.api_info["api_thread"] = api.run_api(self.verbose)

        # check that the MATRX API is set to True if the MATRX visualizer is requested
        elif self.run_matrx_visualizer:
            raise Exception("The MATRX visualizer requires the MATRX API to work. Currently, run_matrx_visualizer=True"
                            " while run_matrx_api=False")

        # startup the MATRX visualizer if requested
        if self.run_matrx_visualizer:
            self.matrx_visualizer_thread = visualization_server.run_matrx_visualizer(self.verbose, media_folder)

        # warn the user if they forgot to turn on the MATRX visualizer
        elif media_folder is not None:
            warnings.warn("A media folder path for the MATRX visualizer was given, but run_matrx_visualizer is set to " \
                          "False denoting that the default visualizer should not be run.")

    def stop(self):
        """ Stop any world-overarching MATRX scripts, such as, if started, the api or MATRX visualization.
        Returns
        -------
        """
        if self.run_matrx_api:
            print("Shutting down Matrx api")
            r = requests.get("http://localhost:" + str(api.port) + "/shutdown_API")
            self.api_info["api_thread"].join()

        if self.run_matrx_visualizer:
            print("Shutting down Matrx visualizer")
            r = requests.get("http://localhost:" + str(visualization_server.port) + "/shutdown_visualizer")
            self.matrx_visualizer_thread.join()


class RandomProperty:

    def __init__(self, values, distribution=None, allow_duplicates=True):

        # If distribution is None, its uniform (equal probability to all values)
        if distribution is None:
            distribution = [1 / len(values) for _ in values]

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

        # Since the value choice is selected using Numpy, the choice may have changed to a unserializable numpy object
        # which would prevent it the be 'jsonified' for the API. So we check for this and cast it to its Python version.
        if all(isinstance(n, int) for n in self.values):
            choice = int(choice)
        elif all(isinstance(n, float) for n in self.values):
            choice = float(choice)

        self.selected_values.add(choice)
        return choice

    def reset(self):
        self.selected_values = set()


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


def _perlin_noise(min_x, max_x, min_y, max_y, rng):
    """
    Source; https://stackoverflow.com/questions/42147776/producing-2d-perlin-noise-with-numpy
    Parameters
    ----------
    min_x
    max_x
    min_y
    max_y
    seed

    Returns
    -------

    """

    def lerp(a, b, x_):
        """linear interpolation"""
        return a + x_ * (b - a)

    def fade(t):
        """6t^5 - 15t^4 + 10t^3"""
        return 6 * t ** 5 - 15 * t ** 4 + 10 * t ** 3

    def gradient(h, x_, y):
        """grad converts h to the right gradient vector and return the dot product with (x,y)"""
        vectors = np.array([[0, 1], [0, -1], [1, 0], [-1, 0]])
        g = vectors[h % 4]
        return g[:, :, 0] * x_ + g[:, :, 1] * y

    # Create coordinate grid
    x_steps = int(max_x - min_x)
    y_steps = int(max_y - min_y)
    y, x = np.meshgrid(np.linspace(min_x, max_x, x_steps, endpoint=False),
                       np.linspace(min_y, max_y, y_steps, endpoint=False))

    # permutation table
    p = np.arange(256, dtype=int)
    rng.shuffle(p)
    p = np.stack([p, p]).flatten()
    # coordinates of the top-left
    noise_size = 1
    xi = np.array([np.array([int(i / noise_size) * noise_size] * x_steps) for i, _ in enumerate(range(x.shape[0]))])
    yi = np.array([np.array([int(i / noise_size) * noise_size] * x_steps) for i, _ in enumerate(range(y.shape[0]))])
    # internal coordinates
    xf = x - xi
    yf = y - yi
    # fade factors
    u = fade(xf)
    v = fade(yf)
    # noise components
    n00 = gradient(p[p[xi] + yi], xf, yf)
    n01 = gradient(p[p[xi] + yi + 1], xf, yf - 1)
    n11 = gradient(p[p[xi + 1] + yi + 1], xf - 1, yf - 1)
    n10 = gradient(p[p[xi + 1] + yi], xf - 1, yf)
    # combine noises
    x1 = lerp(n00, n10, u)
    x2 = lerp(n01, n11, u)
    return lerp(x1, x2, v)


def _white_noise(min_x, max_x, min_y, max_y, rng):
    noise_table = rng.normal(size=[max_x - min_x, max_y - min_y])
    return noise_table
