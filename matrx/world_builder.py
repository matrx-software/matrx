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
from matrx.objects.standard_objects import Wall, Door, AreaTile, SmokeTile, CollectionDropOffTile, CollectionTarget
from matrx.goals.goals import LimitedTimeGoal, WorldGoal, CollectionGoal

import matrx.defaults as defaults

# addons
from matrx.api import api
from matrx_visualizer import visualization_server


class WorldBuilder:
    """ Used to create one or more worlds according to a single blueprint.
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
        shape: tuple or list
            Denotes the width and height of the world you create.

        tick_duration: float (optional, default 0.5)
            The duration of a single 'tick' or loop in the game-loop of the
            world you create.

        random_seed: int, (optional, default 1)
            The master random seed on which all objects, agents and worlds are
            seeded. Should be a positive non-zero integer.

        simulation_goal: WorldGoal, int, list or tuple (optional, default 1000)
            The goal or goals of the world, either a single `WorldGoal`, a
            list of such or a positive non-zero integer to denote the maximum
            number of 'ticks' the world(s) has to run.

        run_matrx_api: bool (optional, default True)
            Whether to run the API. This API is used to connect the default
            MATRX visualizer or a custom one.

        run_matrx_visualizer: bool (optional, default False)
            Whether to run the default MATRX visualizer, this requires the API
            to be run. When set to True, it starts the visualization that is
            accessible through http://localhost:3000.

        visualization_bg_clr: string (optional, default "C2C2C2")
            The color of the world when visualized using MATRX' own
            visualisation server. A string representation of hexadecimal color.

        visualization_bg_img: string (optional, None)
            An optional background image of the world when visualized using
            MATRX' own visualisation server. A string of the path to the image
            file. When None, no background image is used.

        verbose: bool (optional, False)
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
            >>> builder = WorldBuilder(shape=(10, 10), random_seed=42, tick_duration=-1, visualization_bg_clr="#000000")

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

        # If world goal is an integer, we create a LimitedTimeGoal with
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
        :meth:`matrx.grid_world.GridWorld.run`:
            Start a GridWorld instance.
        """

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
        :any:`matrx.logger.GridWorldLogger`:
            The interface class to which the passed `logger_class` should
            from. inherit
        :any:`matrx.logger`:
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
        >>> builder.add_logger(LogIdleAgents, log_strategy=GridWorldLogger.LOG_ON_GOAL_REACHED)

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

        **custom_properties: dict (optional, None)
            Any additional given keyword arguments will be encapsulated in
            this dictionary. These will be added to the AgentBody as
            custom_properties which can be perceived by other agents and
            objects or which can be used or altered (if allowed to by the
            customizable_properties list) by the AgentBrain or others.

        Raises
        ------
        ValueError
            When the given location is not of form (x, y).
            When the given agent brain does not inheret from `AgentBrain`
            When the given name was already assigned to a previous added agent.

        Examples
        --------

        Add a simple patrolling agent that patrols the world.

        >>> from matrx import WorldBuilder
        >>> from matrx.agents import PatrollingAgentBrain
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> waypoints = [(0, 0), (10, 0), (10, 10), (0, 10)]
        >>> brain = PatrollingAgentBrain(waypoints)
        >>> builder.add_agent((5, 5), brain, name="Patroller")

        Add an agent with some custom property `foo="bar"` and w.

        >>> from matrx import WorldBuilder
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

        custom_properties: dict or list (optional, default None)
            A dictionary of custom properties and their values for all agents
            or a list of such dictionaries for every agent.

        sense_capability: SenseCapability or list (optional, default None)
            A single `SenseCapability` used for every agent, or a list of those
            for every given agent.

        customizable_properties: list (optional, default None)
            A list of property names that each agent can edit. When it is a
            list of listed properties, it denotes a unique set of customizable
            properties for every agent.

        is_traversable: bool or list (optional, default None)
            A list of booleans or a single boolean denoting either for each
            agent or all agents their traversability.

        visualize_size: float or list (optional, default None)
            A list of floats or a single float denoting either for each
            agent or all agents their traversability. A value of 0.0 means no
            size, and a value of 1.0 fills the entire tile.

        visualize_shape: int, string or list (optional, default None)
            The shape of the agents in the visualisation. When a list, denotes
            the shape of every agent. Depending on the value it obtains this
            shape:

            * 0 = a square

            * 1 = a triangle

            * 2 = a circle

            * Path to image or GIF = that image scaled to match the size.

        visualize_colour: string or list (optional, default None)
            The colours the agents in the visualisation. When a list, denotes
            the colour separately of every agent. Should be a string
            hexadecimal colour value.

        visualize_opacity: float or list (optional, default None)
            The opacities of the agents in the visualization. When a list,
            denotes the opacity separately of every agent A value of 1.0
            means full opacity and 0.0 no opacity.

        visualize_when_busy: bool or list (optional, default None)
            Whether to visualize when an agent is busy with a action. True
            means show this using a loading icon, false means do not show
            this in the visualizer. When a list, specifies this for every
            agent separately.

        Raises
        ------
        ValueError
            When a given location is not of form (x, y).
            When a given agent brain does not inheret from `AgentBrain`
            When a given name was already assigned to a previous added agent.

        Examples
        --------

        Add a team of three agents:
        >>> from matrx import WorldBuilder
        >>> from matrx.agents import AgentBrain
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> brains = [AgentBrain() for _ in range(3)]
        >>> locs = [(0, 0), (1, 1), (2, 2)]
        >>> builder.add_team(brains, locs, "The A Team")

        """
        self.add_multiple_agents(agent_brains, locations,
                                 custom_properties=custom_properties,
                                 sense_capabilities=sense_capability,
                                 customizable_properties=customizable_properties,
                                 is_traversable=is_traversable,
                                 teams=team_name,
                                 visualize_sizes=visualize_size,
                                 visualize_shapes=visualize_shape,
                                 visualize_colours=visualize_colour,
                                 visualize_opacities=visualize_opacity,
                                 visualize_when_busy=visualize_when_busy)

    def add_multiple_agents(self, agents, locations, custom_properties=None,
                            sense_capabilities=None,
                            customizable_properties=None,
                            is_traversable=None,
                            teams=None, visualize_sizes=None,
                            visualize_shapes=None,
                            visualize_colours=None, visualize_opacities=None,
                            visualize_depths=None,
                            visualize_when_busy=None):
        """ Add multiple agents to the world.

        Parameters
        ----------
        agents: list or tuple
            The list or tuple of agent brains that will control each agent.
            Should be of the same size as `locations`.

        locations: list or tuple
            The list or tuple of all agent locations.

        custom_properties: dict or list (optional, default None)
            A dictionary of custom properties and their values for all agents
            or a list of such dictionaries for every agent.

        sense_capability: SenseCapability or list (optional, default None)
            A single `SenseCapability` used for every agent, or a list of those
            for every given agent.

        customizable_properties: list (optional, default None)
            A list of property names that each agent can edit. When it is a
            list of listed properties, it denotes a unique set of customizable
            properties for every agent.

        is_traversable: bool or list (optional, default None)
            A list of booleans or a single boolean denoting either for each
            agent or all agents their traversability.

        teams: string or list (optional, default None)
            The team name of all agents or a list of the team for every
            separate agent.

        visualize_sizes: float or list (optional, default None)
            A list of floats or a single float denoting either for each
            agent or all agents their traversability. A value of 0.0 means no
            size, and a value of 1.0 fills the entire tile.

        visualize_shapes: int, string or list (optional, default None)
            The shape of the agents in the visualisation. When a list, denotes
            the shape of every agent. Depending on the value it obtains this
            shape:

            * 0 = a square

            * 1 = a triangle

            * 2 = a circle

            * Path to image or GIF = that image scaled to match the size.

        visualize_colours: string or list (optional, default None)
            The colours the agents in the visualisation. When a list, denotes
            the colour separately of every agent. Should be a string
            hexadecimal colour value.

        visualize_opacities: float or list (optional, default None)
            The opacities of the agents in the visualization. When a list,
            denotes the opacity separately of every agent A value of 1.0
            means full opacity and 0.0 no opacity.

        visualize_depths: int or list (optional, default None)
            The visualization depths of the agents. When a list, denotes the
            depths separately of every agent. Larger values, means that they
            will be visiualized on top.

        visualize_when_busy: bool or list (optional, default None)
            Whether to visualize when an agent is busy with a action. True
            means show this using a loading icon, false means do not show
            this in the visualizer. When a list, specifies this for every
            agent separately.

        Raises
        ------
        ValueError
            When a given location is not of form (x, y).
            When a given agent brain does not inheret from `AgentBrain`
            When a given name was already assigned to a previous added agent.

        Examples
        --------

        Add a team of three agents:
        >>> from matrx import WorldBuilder
        >>> from matrx.agents import AgentBrain
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> brains = [AgentBrain() for _ in range(3)]
        >>> locs = [(0, 0), (1, 1), (2, 2)]
        >>> builder.add_team(brains, locs, "The A Team")

        """

        # If any of the lists are not given, fill them with None and if they
        # are a single value of its expected type we copy it in a list. A none
        # value causes the default value to be loaded.
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

    def add_agent_prospect(self, location, agent, probability, name="Agent",
                           customizable_properties=None, sense_capability=None,
                           is_traversable=None, team=None,
                           possible_actions=None, is_movable=None,
                           visualize_size=None, visualize_shape=None,
                           visualize_colour=None, visualize_opacity=None,
                           visualize_depth=None, visualize_when_busy=None,
                           **custom_properties):
        """ Adds an agent to the world's blueprint given a probability.

        This methods adds an agent body to every created world at the specified
        location and linked to an instance of the provided agent brain. It does
        so based on the provided probability. Meaning that there is
        `probability` chance that the agent will be added on the specified
        location.

        All keyword parameters default to None. Which means that their values
        are obtained from their similar named constants in `matrx.defaults`.

        Parameters
        ----------
        location: tuple or list
            The location (x,y) of the to be added agent.

        agent_brain: AgentBrain
            The AgentBrain instance that will control the agent.

        probability: float
            A float between 0.0 and 1.0. Denotes the probability with which
            to add this agent when a world is created.

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
             Whether this agent can be moved by other agents, for example by
             picking it up and dropping it.

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

        **custom_properties: dict (optional, None)
            Any additional given keyword arguments will be encapsulated in
            this dictionary. These will be added to the AgentBody as
            custom_properties which can be perceived by other agents and
            objects or which can be used or altered (if allowed to by the
            customizable_properties list) by the AgentBrain or others.

        Raises
        ------
        ValueError
            When the given location is not of form (x, y).
            When the given agent brain does not inheret from `AgentBrain`
            When the given name was already assigned to a previous added agent.

        Examples
        --------

        Add an agent with 50% chance of being added to the world.
        >>> from matrx import WorldBuilder
        >>> from matrx.agents import AgentBrain
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> brain = AgentBrain()
        >>> builder.add_agent_prospect((5, 5), brain, 0.5, name="Agent", \
        >>>     foo="bar")

        """

        # Add agent as normal
        self.add_agent(location, agent, name, customizable_properties,
                       sense_capability, is_traversable, team,
                       possible_actions, is_movable, visualize_size,
                       visualize_shape, visualize_colour, visualize_depth,
                       visualize_opacity, visualize_when_busy,
                       **custom_properties)

        # Get the last settings (which we just added) and add the probability
        self.agent_settings[-1]['probability'] = probability

    def add_object(self, location, name, callable_class=None,
                   customizable_properties=None, is_traversable=None,
                   is_movable=None, visualize_size=None, visualize_shape=None,
                   visualize_colour=None, visualize_depth=None,
                   visualize_opacity=None, **custom_properties):
        """ Adds an environment object to the blueprint.

        This environment object can be any object that is a `EnvObject` or
        inherits from it.

        All optional parameters default to None, meaning that their values are
        taken from `matrx.defaults`.

        Parameters
        ----------
        location: list or tuple
            The location of the object of the form (x,y).

        name: string
            The name of the object.

        callable_class: class
            A class object of the to be added object. Should be `EnvObject` or
            any class that inherits from this.

        customizable_properties: list (optional, None)
            A list or tuple of names of properties for this object that can be
            altered or customized. Either by an agent, itself or other objects.
            If a property value gets changed that is not in this list than an
            exception is thrown.

        is_traversable: bool (optional, default None)
            Whether this object allows other (traversable) agents and objects
            to be at the same location.

        is_movable: bool (optional, default None)
            Whether this object can be moved by an agent. For example, by
            picking it up and dropping it.

        visualize_shape: int or string (optional, None)
            The shape of this object in its visualisation. Depending on the
            value it obtains this shape:

            * 0 = a square

            * 1 = a triangle

            * 2 = a circle

            * Path to image or GIF = that image scaled to match the size.

        visualize_colour: string (optional, None)
            The colour of this object in its visualisation. Should be a string
            hexadecimal colour value.

        visualize_depth: int (optional, None)
            The visualisation depth of this object in its visualisation. It
            denotes the 'layer' on which it is visualized. A larger value is
            more on 'top'.

        visualize_opacity: float (optional, None)
            The opacity of this object in its visualization. A value of 1.0
            means full opacity and 0.0 no opacity.

        **custom_properties: dict (optional, None)
            Any additional given keyword arguments will be encapsulated in
            this dictionary. These will be added to the AgentBody as
            custom_properties which can be perceived by other agents and
            objects or which can be used or altered (if allowed to by the
            customizable_properties list) by the AgentBrain or others.

        Raises
        ------
            AssertionError
                When the location is not a list or tuple.
                When the callable_class is not callable.

        Examples
        --------
        Add a standard EnvObject:
        >>> from matrx import WorldBuilder
        >>> from matrx.objects import EnvObject
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> builder.add_object((4, 4), "Object", EnvObject)

        """

        if callable_class is None:
            callable_class = EnvObject

        # Check if location and agent are of correct type
        assert isinstance(location, list) or isinstance(location, tuple)
        assert isinstance(callable_class, Callable)

        # Check if location only contains integers, otherwise warn use and
        # cast to int
        if not (isinstance(location[0], int) and isinstance(location[1], int)):
            warnings.warn(f"The location {location} of {name} should contain "
                          f"only integers, encountered {str(type(location[0]))}"
                          f" and {str(type(location[1]))} . Casting these to "
                          f"integers resulting in "
                          f"{(int(location[0]), int(location[1]))}")
            location = (int(location[0]), int(location[1]))

        # Load default parameters if not passed
        if is_movable is None:
            is_movable = defaults.ENVOBJECT_IS_MOVABLE

        # If default variables are not given, assign them (most empty, except
        # of sense_capability that defaults to all objects with infinite
        # range).
        if custom_properties is None:
            custom_properties = {}
        if customizable_properties is None:
            customizable_properties = []

        # Define a settings dictionary with all we need to register and add
        # an agent to the GridWorld
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

    def add_object_prospect(self, location, name, probability,
                            callable_class=None, customizable_properties=None,
                            is_traversable=None, is_movable=None,
                            visualize_size=None, visualize_shape=None,
                            visualize_colour=None, visualize_depth=None,
                            visualize_opacity=None, **custom_properties):
        """ Adds an object to the blueprint with a certain probability.

        This methods adds an object to every created world at the specified
        location. It does so based on the provided probability. Meaning that
        there is `probability` chance that the agent will be added on the
        specified location.

        All keyword parameters default to None. Which means that their values
        are obtained from their similar named constants in `matrx.defaults`.

        Parameters
        ----------
        location: list or tuple
            The location of the object of the form (x,y).

        name: string
            The name of the object.

        probability: float
            A float between 0.0 and 1.0 that denotes the probability of adding
            this object to the world when it is created.

        callable_class: class
            A class object of the to be added object. Should be `EnvObject` or
            any class that inherits from this.

        customizable_properties: list (optional, None)
            A list or tuple of names of properties for this object that can be
            altered or customized. Either by an agent, itself or other objects.
            If a property value gets changed that is not in this list than an
            exception is thrown.

        is_traversable: bool (optional, default None)
            Whether this obejct allows other (traversable) agents and objects
            to be at the same location.

        is_movable: bool (optional, None)
             Whether this agent can be moved by other agents, for example by
             picking it up and dropping it.

        visualize_shape: int or string (optional, None)
            The shape of this object in its visualisation. Depending on the
            value it obtains this shape:

            * 0 = a square

            * 1 = a triangle

            * 2 = a circle

            * Path to image or GIF = that image scaled to match the size.

        visualize_colour: string (optional, None)
            The colour of this object in its visualisation. Should be a string
            hexadecimal colour value.

        visualize_depth: int (optional, None)
            The visualisation depth of this object in its visualisation. It
            denotes the 'layer' on which it is visualized. A larger value is
            more on 'top'.

        visualize_opacity: float (optional, None)
            The opacity of this object in its visualization. A value of 1.0
            means full opacity and 0.0 no opacity.

        **custom_properties: dict (optional, None)
            Any additional given keyword arguments will be encapsulated in
            this dictionary. These will be added to the AgentBody as
            custom_properties which can be perceived by other agents and
            objects or which can be used or altered (if allowed to by the
            customizable_properties list) by the AgentBrain or others.

        Raises
        ------
            AssertionError
                When the location is not a list or tuple.
                When the callable_class is not callable.

        Examples
        --------
        Add a standard EnvObject with a 50% probability:
        >>> from matrx import WorldBuilder
        >>> from matrx.objects import EnvObject
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> builder.add_object_prospect((4, 4), "Object", 0.5, EnvObject)

        """

        # Add object as normal
        self.add_object(location, name, callable_class,
                        customizable_properties, is_traversable, is_movable,
                        visualize_size, visualize_shape, visualize_colour,
                        visualize_depth, visualize_opacity,
                        **custom_properties)

        # Get the last settings (which we just added) and add the probability
        self.object_settings[-1]['probability'] = probability

    def add_multiple_objects(self, locations, names=None,
                             callable_classes=None, custom_properties=None,
                             customizable_properties=None, is_traversable=None,
                             visualize_sizes=None, visualize_shapes=None,
                             visualize_colours=None, visualize_depths=None,
                             visualize_opacities=None, is_movable=None):
        """ Add several objects to the blueprint.

        These environment objects can be any object that is an `EnvObject` or
        inherits from it.

        All optional parameters default to None, meaning that their values are
        taken from `matrx.defaults`.

        Parameters
        ----------
        locations: tuple or list
            A tuple or list of the form [(x, y), ...] specifying each object's
            location.

        names: string or list (optional, default None)
            A single name for all objects or a list of names for every object.
            When None, defaults to the name of the provided `callable_classes`.

        callable_classes: EnvObject or list (optional, default None)
            A single class specifying a environment object or a list of classes
            for every object. When None, defaults to EnvObject

        custom_properties: dict or list (optional, None)
            A dictionary containing all custom property names and their values
            of a list of such dictionaries for every object.

        customizable_properties: list (optional, None)
            A list of properties that agents and objects are allowed to change
            or a list of such lists for every object.

        is_traversable: bool or list (optional, None)
            Whether all objects are traversable or a list of such booleans to
            specify this for every object.

        visualize_sizes: float or list (optional, None)
            The size of all objects or a list of such sizes for every object.

        visualize_shapes: int, string or list (optional, None)
            The shape of the objects in the visualisation or list of shapes for
            every object. Depending on the value it obtains this shape:

            * 0 = a square

            * 1 = a triangle

            * 2 = a circle

            * Path to image or GIF = that image scaled to match the size.

        visualize_colours: string or list (optional, None)
            The colour of the objects or a list of such colours. As a
            hexidecimal string.

        visualize_depths: int or list (optional, None)
            The visualisation depth of the objects in the visualisation or a
            list of such depths for every object. It denotes the 'layer' on
            which it is visualized. A larger value is more on 'top'.

        visualize_opacities: float (optional, None)
            The opacity of the objects in the visualisation or a list of
            opacities for every object. A value of 1.0 means full opacity and
            0.0 no opacity.

        is_movable: bool or list (optional, None)
            Whether the objects can be moved by an agent or list denoting this
            for every object. For example, by picking it up and dropping it.

        Raises
        ------
            AssertionError
                When the location is not a list or tuple.
                When the callable_class is not callable.

        Examples
        --------
        Add three standard environment objects with the same name:
        >>> from matrx import WorldBuilder
        >>> from matrx.objects import EnvObject
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> locs = [(1, 1), (2, 2), (3, 3)]
        >>> builder.add_multiple_objects(locs, "Object", EnvObject)

        """

        # If any of the lists are not given, fill them with None and if they
        # are a single value of its expected type we copy it in a list. A none
        # value causes the default value to be loaded.
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

    def add_human_agent(self, location, agent, name="HumanAgent",
                        customizable_properties=None, sense_capability=None,
                        is_traversable=None, team=None, possible_actions=None,
                        is_movable=None, visualize_size=None,
                        visualize_shape=None, visualize_colour=None,
                        visualize_depth=None, visualize_opacity=None,
                        visualize_when_busy=None, key_action_map=None,
                        **custom_properties):
        """ Adds an agent that can be controlled by a human user.

        This methods adds an agent body to every created world at the specified
        location and linked to an instance of a `HumanAgentBrain` which handles
        user input as received from a visualisation.

        All keyword parameters default to None. Which means that their values
        are obtained from their similar named constants in `matrx.defaults`.

        Parameters
        ----------
        location: tuple or list
            The location (x,y) of the to be added agent.

        agent: HumanAgentBrain
            The human agent brain that is linked to this agent. Should be of
            type `HumanAgentBrain` or inherit from it.

        name: string (optional, default "HumanAgent")
            The name of the agent, should be unique to allow the visualisation
            to have a single web page per agent. If the name is already used,
            an exception is raised.

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

        key_action_map: dict (optional, None)
            A dictionary that maps keyboard keys in ASCII to action classes. It
            can be used to translate keystrokes to the agent performing a
            certain action.

        **custom_properties: dict (optional, None)
            Any additional given keyword arguments will be encapsulated in
            this dictionary. These will be added to the AgentBody as
            custom_properties which can be perceived by other agents and
            objects or which can be used or altered (if allowed to by the
            customizable_properties list) by the AgentBrain or others.

        Raises
        ------
            ValueError
                When an agent with the given name was already added previously.
                When the `agent` parameter does not inherits from
                `HumanAgentBrain`

        Examples
        --------

        Add a standard human controlled agent:
        >>> from matrx import WorldBuilder
        >>> from matrx.agents import HumanAgentBrain
        >>> builder = WorldBuilder(shape=(10, 10)))
        >>> brain = HumanAgentBrain()
        >>> builder.add_human_agent((5, 5), brain, name="Neo")

        Add a human controlled agent with a custom key map:
        >>> from matrx import WorldBuilder
        >>> from matrx.agents import HumanAgentBrain
        >>> from matrx.actions import *
        >>> builder = WorldBuilder(shape=(10, 10)))
        >>> brain = HumanAgentBrain()
        >>> keymap = {8: MoveNorth, 6: MoveEast, 2: MoveSouth, 4: MoveWest}
        >>> builder.add_human_agent((5, 5), brain, name="Morpheus", \
        >>>     key_action_map=keymap)

        """

        # Check if location and agent are of correct type
        assert isinstance(location, list) or isinstance(location, tuple)
        assert isinstance(agent, HumanAgentBrain)

        for existingAgent in self.agent_settings:
            if existingAgent["mandatory_properties"]["name"] == name:
                raise Exception(f"A human agent with the name {name} was "
                                f"already added. Agent names should be "
                                f"unique.", name)
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

        # If default variables are not given, assign them (most empty, except
        # of sense_capability that defaults to all objects with infinite range).
        if custom_properties is None:
            custom_properties = {}
        if sense_capability is None:
            sense_capability = create_sense_capability([], [])  # Create sense capability that perceives all
        if customizable_properties is None:
            customizable_properties = []

        # Check if the agent is of HumanAgent, if not; use the add_agent method
        inh_path = _get_inheritence_path(agent.__class__)
        if 'HumanAgent' not in inh_path:
            ValueError(f"You are adding an agent that does not inherit from HumanAgent with the name {name}. Use "
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

    def add_area(self, top_left_location, width, height, name,
                 customizable_properties=None, visualize_colour=None,
                 visualize_opacity=None, **custom_properties):
        """ Adds an area of tiles/surface.

        Adds multiple `AreaTile` objects inside the specified square, including
        the edges under a single common name.

        All keyword parameters default to None. Which means that their values
        are obtained from their similar named constants in `matrx.defaults`.

        Parameters
        ----------
        top_left_location: list or tuple
            A location of the form (x, y) that specifies the top-left location
            of the rectangle.

        width: int
            The width in number of grid squares.

        height: int
            The height in number of grid squares.

        name: string
            The name of the area.

        customizable_properties: list (optional, default None)
            The properties that agents and objects can modify in all the
            created tiles.

        visualize_colour: string (optional, default None)
            The colour of the tiles as a hexidecimal string.

        visualize_opacity: float (optional, default None)
            The opacity of the tiles. A value of 1.0 means full opacity and
            0.0 no opacity.

        **custom_properties: list (optional, None)
        Any additional given keyword arguments will be encapsulated in
        this dictionary. These will be added to all the tiles as
        custom_properties which can be perceived by other agents and
        objects or which can be used or altered (if allowed to by the
        customizable_properties list) by agents or objects.

        Raises
        ------
            AssertionError
                When the location is not a list or tuple.
                When the callable_class is not callable.

            ValueError
                When the width or height is less then 1.

        Examples
        --------

        Add a green area to the world:
        >>> from matrx import WorldBuilder
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> builder.add_area((3,3), 3, 3, "Grass", visualize_colour="#00a000")

        """

        # Check if width and height are large enough to make an actual room
        # (with content)
        if width < 1 or height < 1:
            raise Exception(f"While adding area {name}; The width {width} "
                            f"and/or height {height} should both be larger "
                            f"than 0.")

        # Get all locations in the rectangle
        locs = self.__list_area_locs(top_left_location, width, height)

        # Add all area objects
        self.add_multiple_objects(locations=locs, callable_classes=AreaTile,
                                  names=name,
                                  customizable_properties=customizable_properties,
                                  visualize_colours=visualize_colour,
                                  visualize_opacities=visualize_opacity,
                                  custom_properties=custom_properties)

    def add_smoke_area(self, top_left_location, width, height, name,
                       visualize_colour=None, smoke_thickness_multiplier=1.0,
                       visualize_depth=None, **custom_properties):
        """ Adds a smoke-like area.

        This method adds an area where the opacity of the added `SmokeTile`
        follow a white noise pattern, mimicking the idea of a fog or body of
        water.

        Parameters
        ----------
        top_left_location: list or tuple
            A location of the form (x, y) that specifies the top-left location
            of the rectangle.

        width: int
            The width in number of grid squares.

        height: int
            The height in number of grid squares.

        name: string
            The name of the area.

        visualize_colour: string (optional, default None)
            The colour of the tiles as a hexadecimal string.

        visualize_depth: int (optional, default None)
            The visualisation depth of the area in the visualisation. It
            denotes the 'layer' on which it is visualized. A larger value is
            more on 'top'.

        **custom_properties: list (optional, None)
        Any additional given keyword arguments will be encapsulated in
        this dictionary. These will be added to all the tiles as
        custom_properties which can be perceived by other agents and
        objects or which can be used or altered (if allowed to by the
        customizable_properties list) by agents or objects.

        Raises
        ------
            AssertionError
                When the location is not a list or tuple.
                When the callable_class is not callable.

        Examples
        --------

        Add an area resembling a body of water:
        >>> from matrx import WorldBuilder
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> builder.add_smoke_area((3,3), 3, 3, "Lake", \
        >>>     visualize_colour="#0050a0")

        """
        # Check if width and height are large enough to make an actual room
        # (with content)
        if width < 1 or height < 1:
            raise Exception(f"While adding area {name}; The width {width} "
                            f"and/or height {height} should both be larger"
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
                self.add_object(location=[x, y], name=name,
                                callable_class=SmokeTile,
                                visualize_colour=visualize_colour,
                                visualize_opacity=opacity,
                                visualize_depth=visualize_depth,
                                **custom_properties)

    def add_line(self, start, end, name, callable_class=None,
                 customizable_properties=None, is_traversable=None,
                 is_movable=None, visualize_size=None, visualize_shape=None,
                 visualize_colour=None, visualize_depth=None,
                 visualize_opacity=None, **custom_properties):
        """ Adds a line of objects to the blueprint.

        This line can be under any angle, and all locations crossed by that
        line will have an object.

        All keyword parameters default to None. Which means that their values
        are obtained from their similar named constants in `matrx.defaults`.

        Parameters
        ----------
        start: list or tuple
            A location of form (x, y) denoting the start of the line.
        end
            A location of form (x, y) denoting the end of the line.

        name: string
            The name of the line of objects.

        callable_class: EnvObject (optional, None)
            The object class denoting the objects that should be added. This
            is `EnvObject` by default or must be any other class or inherit
            from this class.

        customizable_properties: list (optional, None)
            A list or tuple of names of properties for these objects that can
            be altered or customized. Either by an agent, itself or other
            objects. If a property value gets changed that is not in this list,
            an exception is thrown.

        is_traversable: bool (optional, default None)
            Whether this object allows other (traversable) agents and objects
            to be at the same location.

        is_movable: bool (optional, None)
             Whether these objects can be moved by  agents, for example by
             picking it up and dropping it.

        visualize_size: float or list (optional, None)
            The size of all objects or a list of such sizes for every object.

        visualize_shape: int or string (optional, None)
            The shape of this object in its visualisation. Depending on the
            value it obtains this shape:

            * 0 = a square

            * 1 = a triangle

            * 2 = a circle

            * Path to image or GIF = that image scaled to match the size.

        visualize_colour: string (optional, None)
            The colour of this object in its visualisation. Should be a string
            hexadecimal colour value.

        visualize_depth: int (optional, None)
            The visualisation depth of this object in its visualisation. It
            denotes the 'layer' on which it is visualized. A larger value is
            more on 'top'.

        visualize_opacity: float (optional, None)
            The opacity of this object in its visualization. A value of 1.0
            means full opacity and 0.0 no opacity.

        **custom_properties: dict (optional, None)
            Any additional given keyword arguments will be encapsulated in
            this dictionary. These will be added to the AgentBody as
            custom_properties which can be perceived by other agents and
            objects or which can be used or altered (if allowed to by the
            customizable_properties list) by the AgentBrain or others.

        Raises
        ------
            AssertionError
                When the location is not a list or tuple.
                When the callable_class is not callable.

        Examples
        --------
        Add two colored lines in a cross:
        >>> from matrx import WorldBuilder
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> builder.add_line((0, 0), (10, 10), "Line 1")
        >>> builder.add_line((10, 0), (0, 10), "Line 2")

        """

        # Get the coordinates on the given line
        line_coords = _get_line_coords(start, end)

        # Construct the names
        names = [name for _ in line_coords]

        # Add the actual properties
        self.add_multiple_objects(locations=line_coords, names=names,
                                  callable_classes=callable_class,
                                  custom_properties=custom_properties,
                                  customizable_properties=customizable_properties,
                                  is_traversable=is_traversable,
                                  visualize_sizes=visualize_size,
                                  visualize_shapes=visualize_shape,
                                  visualize_colours=visualize_colour,
                                  visualize_opacities=visualize_opacity,
                                  visualize_depths=visualize_depth,
                                  is_movable=is_movable)

    def add_room(self, top_left_location, width, height, name,
                 door_locations=None, with_area_tiles=False, doors_open=False,
                 wall_visualize_colour=None, wall_visualize_opacity=None,
                 wall_custom_properties=None,
                 wall_customizable_properties=None,
                 area_custom_properties=None,
                 area_customizable_properties=None,
                 area_visualize_colour=None, area_visualize_opacity=None):
        """ Adds a rectangular room withs walls and doors.

        This method allows you to create an area surrounded with walls and
        optional doors.

        All keyword parameters default to None. Which means that their values
        are obtained from their similar named constants in `matrx.defaults`.

        Parameters
        ----------
        top_left_location: list or tuple
            A location of the form (x, y) that specifies the top-left location
            of the rectangle.

        width: int
            The width in number of grid squares.

        height: int
            The height in number of grid squares.

        name: string
            The name of the room. Shared with all objects.

        door_locations: list, (optional, None)
            A list of locations on the wall locations that should be replaced
            by doors. When set to None, no doors will be added.

        with_area_tiles: bool (optional, False)
            Whether the area within the walls should be filled with `AreaTile`
            objects. If set to True, the area parameters are used and passed.

        doors_open: bool (optional, False)
            Whether the doors are initially open or closed.

        wall_visualize_colour: string (optional, default None)
            The colour of the walls.

        wall_visualize_opacity: string (optional, default None)
            The opacity of the walls.

        wall_custom_properties: dict (optional, default None)
            A dictionary of custom properties and their values passed to every
            wall object.

        wall_customizable_properties: list (optional, default None)
            A list of property names that other objects and agents are allowed
            to adjust.

        area_custom_properties:  (optional, default None)
            A dictionary of custom properties and their values passed to every
            area object. Only used when area tiles are added.

        area_customizable_properties:  (optional, default None)
            A list of property names that other objects and agents are allowed
            to adjust. Only used when area tiles are added.

        area_visualize_colour:  (optional, default None)
            The colour of the areas as a hexadeciamal string. Only used when
            area tiles are added.

        area_visualize_opacity:  (optional, default None)
            The opacity of the added area tiles. Only used when area tiles are
            added.

        Raises
        ------
            AssertionError
                When the location is not a list or tuple.
                When the callable_class is not callable.

            ValueError
                When the width or height is less then 2.
                When a door location is not inside a wall.

        Examples
        --------

        Add world boundaries around the grid and a single room with a door and
        a green area:
        >>> from matrx import WorldBuilder
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> builder.add_room((0,0), 10, 10, "World bounds")
        >>> builder.add_room((3,3), 3, 3, "Room", door_locations=(4,3), \
        >>>     with_area_tiles=True, area_visualize_colour="#00a000")

        """

        # Check if width and height are large enough to make an actual room
        # (with content)
        if width <= 2 or height <= 2:
            raise ValueError(f"While adding room {name}; The width {width} "
                             f"and/or height {height} should both be larger "
                             f"than 2.")

        # Check if the with_area boolean is True when any area properties are
        # given
        if with_area_tiles is False and (
                area_custom_properties is not None or
                area_customizable_properties is not None or
                area_visualize_colour is not None or
                area_visualize_opacity is not None):
            warnings.warn(f"While adding room {name}: The boolean with_area_"
                          f"tiles is set to {with_area_tiles} while also "
                          f"providing specific area statements. Treating with_"
                          f"area_tiles as True.")
            with_area_tiles = True

        # Subtract 1 from both width and height, since the top left already
        # counts as a size of 1,1
        width = int(width) - 1
        height = int(height) - 1

        # Set corner coordinates
        top_left = (int(top_left_location[0]),
                    int(top_left_location[1]))
        top_right = (int(top_left_location[0]) + int(width),
                     int(top_left_location[1]))
        bottom_left = (int(top_left_location[0]),
                       int(top_left_location[1]) + int(height))
        bottom_right = (int(top_left_location[0]) + int(width),
                        int(top_left_location[1]) + int(height))

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

        # Check if all door locations are at wall locations, if so remove
        # those wall locations
        door_locations = [] if door_locations is None else door_locations
        for door_loc in door_locations:
            if door_loc in all_:
                all_.remove(door_loc)
            else:
                raise ValueError(f"While adding room {name}, the requested "
                                 f"door location {door_loc} is not in a "
                                 f"wall.")

        # Add all walls
        names = [f"{name} - wall@{loc}" for loc in all_]
        if wall_custom_properties is None:
            wall_custom_properties = {"room_name": name}
        else:
            wall_custom_properties = {**wall_custom_properties, "room_name": name}
        self.add_multiple_objects(locations=all_, names=names, callable_classes=Wall,
                                  visualize_colours=wall_visualize_colour,
                                  visualize_opacities=wall_visualize_opacity,
                                  custom_properties=wall_custom_properties,
                                  customizable_properties=wall_customizable_properties)

        # Add all doors
        for door_loc in door_locations:
            self.add_object(location=door_loc, name=f"{name} - door@{door_loc}", callable_class=Door,
                            is_open=doors_open, **{"room_name": name})

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
                          customizable_properties=area_customizable_properties,
                          **{**area_custom_properties, "room_name": name})

    @staticmethod
    def get_room_locations(room_top_left, room_width, room_height):
        """ Returns the locations within a room, excluding walls.

        .. deprecated:: 1.1.0
          `get_room_locations` will be removed in MATRX 1.2.0, it is replaced by
          `matrx.utils.get_room_locations`.

        This is a helper function for adding objects to a room. It returns a
        list of all (x,y) coordinates that fall within the room excluding the
        walls.

        Parameters
        ----------
        room_top_left: tuple, (x, y)
            The top left coordinates of a room, as used to add that room with
            methods such as `add_room`.
        room_width: int
            The width of the room.
        room_height: int
            The height of the room.

        Returns
        -------
        list, [(x,y), ...]
            A list of (x, y) coordinates that are encapsulated in the
            rectangle, excluding walls.

        See Also
        --------
        WorldBuilder.add_room

        """
        warnings.warn("This method is deprecated and will be removed in v1.2.0. It is replaced by"
                      "`matrx.utils.get_room_locations` as of v1.1.0.", DeprecationWarning)
        locs = utils.get_room_locations(room_top_left, room_width, room_height)
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

        # This is a function unique to the human agent, so only set it if the agent is a human agent
        cb_create_context_menu_self = agent.create_context_menu_for_self if mandatory_props['is_human_agent'] else None

        args = {**mandatory_props,
                'isAgent': True,
                'sense_capability': sense_capability,
                'class_callable': agent.__class__,
                'callback_agent_get_action': agent._get_action,
                'callback_agent_set_action_result': agent._set_action_result,
                'callback_agent_observe': agent._fetch_state,
                'callback_agent_log': agent._get_log_data,
                'callback_agent_get_messages': agent._get_messages,
                'callback_agent_set_messages': agent._set_messages,
                'callback_agent_initialize': agent.initialize,
                'callback_create_context_menu_for_other': agent.create_context_menu_for_other,
                'callback_create_context_menu_for_self': cb_create_context_menu_self,
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

            # Check if the values are a RandomProperty. We include a fairly tailored check due to some import issues:
            # Since the WorldBuilder contains the RandomProperty class and this class is imported by several other
            # modules. But some of those modules are in turn also (indirectly) imported by the WorldBuilder. This
            # creates a looping import. To remedy this you can omit importing RandomProperty by using
            # `matrx.WorldBuilder.RandomProperty` however, this creates different class instance then when using
            # `from matrx.WorldBuilder import RandomProperty`. The former creates a `WorldBuilder.RandomProperty` the
            # latter a `RandomProperty` causing an isinstance check to fail. To fix this we also check if the module
            # name `WorldBuilder` is that of the RandomProperty (e.g. is the set RandomProperty indeed from
            # WorldBuilder?) and also check its name (e.g. does this RandomProperty is indeed named 'RandomProperty'?).
            # This is a weaker check than isinstance, as these are referring to two different usages of RandomProperty.
            if isinstance(v, RandomProperty) or (v.__class__.__module__ in RandomProperty.__module__
                                                 and v.__class__.__name__ == RandomProperty.__name__):
                args[k] = v._get_property(self.rng)

        return args

    def __reset_random(self):
        # TODO resets all RandomProperty and RandomLocation, is called after creating a world so all duplicates can be
        # TODO selected again.
        pass

    def startup(self, media_folder=None):
        """ Start the API and default visualization.

        This method allows you to start the API and the default visualization
        if set in the builder's constructor.

        Parameters
        ----------
        media_folder: string
            The path to a folder where additional figures are stored. Providing
            this path makes those media files accessible to MATRX. It is
            required if you pass your figures to object shapes.

        Raises
        ------
            ValueError
                When the visualizer is set to run but without the API running.

        Examples
        --------
        Create a builder with a running API and visualizer and start these,
        referring to a custom media folder.
        >>> from matrx import WorldBuilder
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> media_folder = "media"
        >>> builder.startup(media_folder)

        """
        # startup the MATRX API if requested
        if self.run_matrx_api:
            self.api_info["api_thread"] = api.run_api(self.verbose)

        # check that the MATRX API is set to True if the MATRX visualizer is
        # requested
        elif self.run_matrx_visualizer:
            raise ValueError("The MATRX visualizer requires the MATRX API to "
                             "work. Currently, run_matrx_visualizer=True while"
                             " run_matrx_api=False")

        # startup the MATRX visualizer if requested
        if self.run_matrx_visualizer:
            self.matrx_visualizer_thread = \
                visualization_server.run_matrx_visualizer(self.verbose,
                                                          media_folder)

        # warn the user if they forgot to turn on the MATRX visualizer
        elif media_folder is not None:
            warnings.warn("A media folder path for the MATRX visualizer was "
                          "given, but run_matrx_visualizer is set to False "
                          "denoting that the default visualizer should not be "
                          "run.")

    def stop(self):
        """ Stops the running API and default visualisation gracefully.
        """
        if self.run_matrx_api:
            if self.verbose:
                print("Shutting down Matrx api")
            _ = requests.get("http://localhost:" + str(api.port)
                             + "/shutdown_API")
            self.api_info["api_thread"].join()

        if self.run_matrx_visualizer:
            if self.verbose:
                print("Shutting down Matrx visualizer")
            _ = requests.get("http://localhost:"
                             + str(visualization_server.port)
                             + "/shutdown_visualizer")
            self.matrx_visualizer_thread.join()

    def add_goal(self, world_goal, overwrite=False):
        """ Appends a `WorldGoal` to the worlds this builder creates.

        Parameters
        ----------
        world_goal : WorldGoal or list/tuple of WorldGoal
            A single world goal or a list/tuple of world goals.
        overwrite : bool (default is False)
            Whether to overwrite the already existing goal in the builder.

        Examples
        --------
        Add a single world goal to a builder, overwriting any previously added goals (e.g. through the builder constructor).
        >>> builder.add_goal(LimitedTimeGoal(100), overwrite=True)

        """
        # Check if the simulation_goal is a SimulationGoal, an int or a list or tuple of SimulationGoal
        if not isinstance(world_goal, (int, WorldGoal, list, tuple)) and len(world_goal) > 0:
            raise ValueError(f"The given simulation_goal {world_goal} should be of type {WorldGoal.__name__} "
                             f"or a list/tuple of {WorldGoal.__name__}, or it should be an int denoting the max"
                             f"number of ticks the world should run (negative for infinite).")

        # Add the world goals
        curr_goals = self.world_settings["simulation_goal"]
        if not isinstance(curr_goals, (list, tuple)):
            curr_goals = (curr_goals,)
        if not isinstance(world_goal, (list, tuple)):
            world_goal = (world_goal,)

        if not overwrite:
            goals = curr_goals + world_goal
        else:
            goals = world_goal

        self.world_settings["simulation_goal"] = goals

    def add_collection_goal(self, name, collection_locs, collection_objects, in_order=False,
                            collection_area_colour="#c87800", collection_area_opacity=1.0, overwrite_goals=False):
        """ Adds a goal to the world to collect objects and drop them in a specific area.

        This is a helper method to quickly add a `CollectionGoal` to the world. A `CollectionGoal` will check if a set of
        objects with certain property-value combinations are at specified locations (potentially in a fixed order). To do
        so, location(s) need to be specified that function as such a "drop off zone". This method add to those locations a
        `CollectionDropOffTile` object, which are searched by the `CollectionGoal` and checks if there the specified objects
        are at those tiles.

        In addition, this method receives a list of dictionaries that represent the kind of objects that need to be
        collected. Since objects are described as a set of properties and their values, these dictionaries contain such
        property-value pairs (with the property names as keys, and their values as values).

        Finally, this method adds a `CollectionGoal` that links these collection tiles and the requested objects. This goal
        checks at each tick if the requested objects are at the specified location(s). If multiple locations are given, the
        requested objects can be spread out over all of those locations! For example, if a Red Block and Blue Block need to
        be collected on locations (0, 0) and  (1, 0), the goal will be accomplished if both blocks are at either location
        but also when the Red Block is at (0, 0) and the Blue Block is at (1, 0) or vice versa.

        Parameters
        ----------
        collection_locs : (x, y) or list/tuple of (x, y)
            A single location where the objects need to be collected, or a list/tuple of such locations. A location is a
            list/tuple of two integers, the x- and y-coordinates respectively.
        collection_objects : list/tuple of dicts, or a RandomProperty with such list/tuple
            A list or tuple of dictionaries. Each dictionary represents a the properties and their respective values that
            identify the to be collected object. It can also be a RandomProperty with as values such a list/tuple. This can
            be used to generate a different collection_objects per world creation.
        name : str
            The name of the `CollectionGoal` and the added `CollectionTarget` and `CollectionDropOffTile` objects.
        in_order : bool (default is False)
            Whether the objects need to be collected and dropped of in the order specified by the `collection_objects` list.
            If all objects are present but not dropped in the right order, the goal will not be accomplished if this is set
            to True.
        collection_area_colour : str (default is )
            The colour of the area on the specified locations representing the drop zone.
        collection_area_opacity : float (default is 1.0)
            The opacity of the area on the specified locations representing the drop zone.
        overwrite_goals : bool (default is False)
            Whether any previously added goals to the builder should be discarded/overwritten.

        Examples
        --------
        Add a collection gaol that requires agents to collect 2 objects in order. The first with the color "#ff0000" (red)
        and the second with the color "#0000ff" (blue). Objects can be dropped at either location (0, 0) or (1, 0). The drop
        off are is called "Dropzone".
        >>> order = [{"visualize_colour": "#ff0000"}, {"visualize_colour": "#0000ff"}]
        >>> builder.add_collection_goal("Dropzone", [(0, 0), (1, 0)], order, in_order=True)

        Add two collection goals, each with the same collection zone. The first goal needs to collect two objects with the
        colours "#ff0000" (red) and "##0000ff" (blue). The second goal needs to collect two objects with the custom property
        "is_candy" set to True. Both goals can be satisfied by dropping a red and blue candy, or by dropping a red and blue
        object that are not candies, and two candies with different colours than red or blue.
        >>> colored_objects = [{"visualize_colour": "#ff0000"}, {"visualize_colour": "#0000ff"}]
        >>> builder.add_collection_goal("Colours", [(0, 0), (1, 0)], colored_objects)
        >>> candy_objects = [{"is_candy": True}, {"is_candy": True}]
        >>> builder.add_collection_goal("Candies", [(0, 0), (1, 0)], candy_objects)

        Add a collection goal to collect a red and blue candy but in a different order every time a world is created. The
        two orders defined here are: first red, then blue OR first blue then red.
        >>> different_orders = [[{"visualize_colour": "#ff0000"}, {"visualize_colour": "#0000ff"}], \
        >>>                     [{"visualize_colour": "#0000ff"}, {"visualize_colour": "#ff0000"}]]
        >>> rp_order = RandomProperty(values=different_orders)
        >>> builder.add_collection_goal("Colours", [(0, 0), (1, 0)], rp_order, in_order=True)


        Notes
        -----
        It is important remember that objects might not be traversable, which prevents them from stacking. So if a goal is
        made that request 2 objects to be collected on the same location where both objects are not traversable, the goal
        will never be able to succeed.

        See Also
        --------
        matrx.goals.CollectionGoal
            The `CollectionGoal` that performs the logic of check that all object(s) are dropped at the drop off tiles.
        matrx.objects.CollectionDropTile
            The tile that represents the location(s) where the object(s) need to be dropped.
        matrx.objects.CollectionTarget
            The invisible object representing which object(s) need to be collected and (if needed) in which order.
        """

        # Check if the `collection_locs` parameter is a list of locations. If it is a single location, make a list out
        # of it. If it are no locations, then raise an exception.
        incorrect_locs = True
        if isinstance(collection_locs, (list, tuple)) and len(collection_locs) > 0:  # locs is indeed a list or tuple
            if len(collection_locs) == 2 and isinstance(collection_locs[0], int) and isinstance(collection_locs[1],
                                                                                                int):
                incorrect_locs = False
            else:
                for l in collection_locs:
                    if isinstance(l, (list, tuple)) and len(l) == 2 and isinstance(l[0], int) and isinstance(l[1], int):
                        incorrect_locs = False
        if incorrect_locs:
            raise ValueError(
                "The `collection_locs` parameter must be a  list or tuple of length two (e.g. [x, y]) or a "
                "list of length > 0 containing such lists/tuples (e.g. [[x1, y1], (x2, y2), [x3, y3]]. These "
                "represent the locations of the area in which the objects need to be collected.")

        # Check if the `collection_objects` is a RandomProperty with values a list/tuple of potential orderings as
        # represented by its own list/tuple of dictionaries. In other words, if `collection_objects` is of type
        # [[dict, ...], ...] or a version with tuples instead of lists.
        vals = collection_objects

        # Check if the values are a RandomProperty. We include a fairly tailored check due to some import issues: Since
        # the WorldBuilder contains the RandomProperty class and this is imported by the Goals module (because
        # CollectionGoal imports it), we get a circular import. To fix this, we do not import the RandomProperty in the
        # CollectionGoal, but instead refer to it in its full module path: matrx.WorldBuilder.RandomProperty. This
        # causes the RandomProperty in WorldBuilder to be a different one then the one import in CollectionGoal. The
        # former is of type RandomProperty while the latter is of type WorldBuilder.RandomProperty, failing the
        # isinstance check. To remedy this we check if their classes are in fact from the same module and have the same
        # name which is a bit of "softer" instance check.
        if isinstance(vals, RandomProperty) or (vals.__class__.__module__ in RandomProperty.__module__
                                                and vals.__class__.__name__ == RandomProperty.__name__):
            vals = vals.values
            if not (isinstance(vals, (list, tuple)) and len(vals) > 0  # check if values are a list/tuple of length > 0
                    and isinstance(vals[0], (list, tuple)) and len(vals[0]) > 0  # check if its items are a list/tuple
                    and isinstance(vals[0][0], dict)):  # check if the items in the listed orderings are of dicts
                raise ValueError(
                    "If `collection_objects` is of type `RandomProperty`, the values it samples from should be a list "
                    "of (ordered) dictionaries. In other words; `collection_objects.values` should of type "
                    "[[dict, ...], ...].Representing 'possible_orders[some_specific_order[obj_props1, "
                    "obj_props2, ...], ...]'.")

        # If `collection_objects` is not a random property, it should be a list/tuple containing dicts. In other words,
        # be of type [dict, ...] which represents a specific set of objects that need to be collected.
        elif not (isinstance(vals, (list, tuple)) and len(vals) > 0 and isinstance(vals[0], dict)):
            raise ValueError(
                f"The `collection_objects` must be a list or tuple of length > 0 containing dictionaries that "
                f"represent an object description of the to be collected objects in terms of property-value "
                f"pairs. In other words, `collection_objects` should be of type [dict, ...] but is "
                f"{type(collection_objects)}.")

        # Add the `CollectionDropOffTile` at each of the given locations. These tiles will be used by the
        # `CollectionGoal` to check if all the objects are indeed collected (potentially in the required order as
        # denoted by the order of the `collect_objects` parameter).
        for l in collection_locs:
            self.add_object(location=l, name=name, callable_class=CollectionDropOffTile, collection_area_name=name,
                            is_traversable=True, is_movable=False, visualize_shape=0,
                            visualize_colour=collection_area_colour, visualize_depth=0,
                            visualize_opacity=collection_area_opacity)

        # Add the `CollectionTarget` object with the specified objects to collect. By default, we add it to the first
        # given collection locations.
        target_name = f"{name}_target"
        self.add_object(location=collection_locs[0], name=target_name,
                        callable_class=CollectionTarget, collection_objects=collection_objects,
                        collection_zone_name=name)

        # Create and add the collection goal
        collection_goal = CollectionGoal(name=name, target_name=target_name, in_order=in_order)
        self.add_goal(collection_goal, overwrite=overwrite_goals)


class RandomProperty:
    """ Represents a object property with random values.

    This property is similar to a regular property of any object or agent.
    The difference is that this represents a set of possible values from which
    the builder samples using a uniform or provided distribution when creating
    a new world.

    It allows you to assign a value to a property (custom or not) that is
    different every time a new world is create (e.g. a block that has a
    different colour each time).

    """

    def __init__(self, values, distribution=None, allow_duplicates=True):
        """ Create a random property value instance.

        Parameters
        ----------
        values: list
            A list of possible values.

        distribution: list (optional, default None)
            A list of probabilities for each respective value to be sampled. If
            set to None, a uniform distribution will be used.

        allow_duplicates: bool (optional, default True)
            Whether the values should be sampled a fresh each time a new world
            is created or values that were already sampled should be ignored.
        """

        # Check if values is a list of dicts, if so set a flag for it so we handle it correctly (cast each dict to a
        # list of key-value pair tuples, as these are hashable and recast back to dict when returning value)
        self.__is_dict_values, self.__dict_at_lvl = RandomProperty.__check_for_dict(values)

        # If distribution is None, its uniform (equal probability to all
        # values)
        if distribution is None:
            distribution = [1 / len(values) for _ in values]

        # Normalize distribution if not already
        if sum(distribution) != 1.0:
            distribution = [el / sum(distribution) for el in distribution]

        # Check that the distribution is complete
        assert len(distribution) == len(values)

        # Assign values and distribution
        self.__values = values
        self.__distribution = distribution
        self.__allow_duplicates = allow_duplicates
        self.__selected_values = set()

    def _get_property(self, rng: RandomState, size=None):

        # if values are a list of dicts, we need to change them to tuples which are hashable
        if self.__is_dict_values:
            vals = RandomProperty.__dict_to_tuples(self.__values)
        else:  # if not a dict, we just copy it
            vals = self.__values.copy()

        if not self.__allow_duplicates:
            for it in self.__selected_values:
                vals.remove(it)

        # Sample random index and get its respective value. The method `rng.choice(vals,...)` fails when vals is not a
        # 1-dimensional list. So we just pick a random index from it.
        idx = rng.choice(len(vals), p=self.__distribution, size=size, replace=self.__allow_duplicates)
        choice = vals[idx]

        # Since the value choice is selected using Numpy, the choice may have changed to a unserializable numpy object
        # which would prevent it the be 'jsonified' for the API. So we check for this and cast it to its Python version.
        if all(isinstance(n, int) for n in self.__values):
            choice = int(choice)
        elif all(isinstance(n, float) for n in self.__values):
            choice = float(choice)

        self.__selected_values.add(choice)

        # If values are supposed to be of dict, recast the list of tuples back to such a dict
        if self.__is_dict_values:
            choice = RandomProperty.__tuples_to_dict(choice, dict_at_lvl=self.__dict_at_lvl - 1)

        return choice

    @property
    def values(self):
        return self.__values

    @property
    def distribution(self):
        return self.__distribution

    @property
    def selected_values(self):
        return self.__selected_values

    @property
    def allow_duplicates(self):
        return self.__allow_duplicates

    @classmethod
    def __dict_to_tuples(cls, list_):
        new_list = []
        for v in list_:
            if isinstance(v, (tuple, list)):
                new_list.append(RandomProperty.__dict_to_tuples(v))
            elif isinstance(v, dict):
                new_v = tuple([(k, v) for k, v in v.items()])
                new_list.append(new_v)
            else:
                new_list.append(v)
        tuple_ = tuple(new_list)
        return tuple_

    @classmethod
    def __tuples_to_dict(cls, list_, dict_at_lvl, lvl=0):
        new_list = []
        for v in list_:
            if (lvl + 1) == dict_at_lvl and isinstance(v, tuple):
                new_v = {key: val for key, val in v}
                new_list.append(new_v)
            elif isinstance(v, (tuple, list)):
                new_list.append(RandomProperty.__tuples_to_dict(v, dict_at_lvl, lvl=lvl + 1))
            else:
                new_list.append(v)
        return new_list

    @classmethod
    def __check_for_dict(cls, list_, lvl=0):
        if isinstance(list_, (tuple, list)):
            for v in list_:
                return RandomProperty.__check_for_dict(v, lvl=lvl + 1)
        elif isinstance(list_, dict):
            return True, lvl
        else:
            return False, lvl

    def reset(self):
        self.__selected_values = set()


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
