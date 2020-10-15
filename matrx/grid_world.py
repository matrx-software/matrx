import datetime
import os.path
import warnings
from collections import OrderedDict
import time
import copy

import gevent

from matrx.actions.object_actions import *
from matrx.logger.logger import GridWorldLogger
from matrx.objects.env_object import EnvObject
from matrx.objects.standard_objects import AreaTile
from matrx.messages.message_manager import MessageManager
from matrx.objects.agent_body import _get_all_classes
from matrx.api import api


class GridWorld:
    """  The Gridworld is the representation of the world and the core of MATRX
    """

    def __init__(self, shape, tick_duration, simulation_goal, rnd_seed=1,
                 visualization_bg_clr="#C2C2C2", visualization_bg_img=None, verbose=False, world_id=0):

        """ Create a GridWorld instance.

        With the constructor you can set a number of general properties and
        from the resulting instance you can call numerous methods to add new
        objects and/or agents.

        Parameters
        ----------
        shape : tuple or list
           Denotes the width and height of the world you create.

        tick_duration : float
           The duration of a single 'tick' or loop in the game-loop of the
           world you create.

        simulation_goal : WorldGoal, int, list or tuple
           The goal or goals of the world, either a single `WorldGoal`, a
           list of such or a positive non-zero integer to denote the maximum
           number of 'ticks' the world(s) has to run.

        rnd_seed : bool (optional, default, 1)
            The master random seed set by the WorldBuilder on which all objects, agents and worlds are
            seeded. Should be a positive non-zero integer.

        visualization_bg_clr : string (optional, "C2C2C2")
           The color of the world when visualized using MATRX' own
           visualisation server. A string representation of hexadecimal color.

        visualization_bg_img : string (optional, None)
           An optional background image of the world when visualized using
           MATRX' own visualisation server. A string of the path to the image
           file. When None, no background image is used.

        verbose : bool (optional, False)
           Whether the GridWorld should be verbose and print development logs to the console.

        world_id : int (optional, 0)
           The ID of this world. Every new GridWorld instance should have a unique ID, such that the frontend knows
           when it has to reinitialize the visualization.


        Examples
        --------

        Create a world builder and generate 10 worlds and run them:
        >>> from matrx.world_builder import WorldBuilder
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> for gridworld in builder.worlds():
        >>>     gridworld.run()

        Every `gridworld` received from builder.worlds() is a GridWorld instance.

        """

        self.__tick_duration = tick_duration  # How long each tick should take (process sleeps until this time passed)
        self.__shape = shape  # The width and height of the GridWorld
        self.__visualization_bg_clr = visualization_bg_clr  # The background color of the visualisation
        self.__visualization_bg_img = visualization_bg_img  # The background image of the visualisation
        self.__verbose = verbose  # Set whether we should print anything or not
        self.world_id = world_id  # ID of this simulation world

        self.__teams = {}  # dictionary with team names (keys), and agents in those teams (values)
        self.__registered_agents = OrderedDict()  # The dictionary of all existing agents in the GridWorld
        self.__environment_objects = OrderedDict()  # The dictionary of all existing objects in the GridWorld

        # The simulation goal, the simulation ends when this/these are reached.
        # Copy and reset all simulation goals, this to make sure that this world has its own goals independent of any
        # other world that potentially received the same simulation goal instance (or list of them)
        if isinstance(simulation_goal, (tuple, list)):
            self.__simulation_goal = [sg.reset() for sg in simulation_goal]
        else:
            self.__simulation_goal = simulation_goal.reset()

        # Get all actions within all currently imported files
        self.__all_actions = _get_all_classes(Action, omit_super_class=True)

        # Initialise an empty grid, a simple 2D array with ID's
        self.__grid = np.array([[None for _ in range(shape[0])] for _ in range(shape[1])])

        self.__api_info = None  # Dict containing info about the API instance
        self.__run_matrx_api = False  # Bool if API is running
        self.__loggers = []  # a list of GridWorldLogger use to log the data
        self.__is_done = False  # Whether the simulation is done (goal(s) reached)
        self.__rnd_seed = rnd_seed  # The random seed of this GridWorld
        self.__rnd_gen = np.random.RandomState(seed=self.__rnd_seed)  # The random state of this GridWorld
        self.__curr_tick_duration = 0.  # Duration of the current tick
        self.__current_nr_ticks = 0  # The number of tick this GridWorld has ran already
        self.__is_initialized = False  # Whether this GridWorld is already initialized
        self.__message_buffer = {}  # dictionary of messages that need to be send to agents, with receiver ids as keys
        self.message_manager = MessageManager()  # keeps track of all messages and makes them available to the api

    def initialize(self, api_info):
        """ Initializes the gridworld instance and any connected visualizations via the API, then pauses the GridWorld.

        By default the GridWorld starts paused. To make it possible for the user to see the first tick of the
        GridWorld, before pressing play and starting the simulation, this function initializes the gridworld to
        tick 0, after which it updates any visualizations via the API, followed by pausing the GridWorld.

        Parameters
        ----------
        api_info : dictionary
           A dictionary which contians information on the API. At least containing the `api_thread` key with the
           API thread, and the `run_matrx_api` key which contains whether the GridWorld should start paused or not.

           Optionally the `nr_states_to_store` key telling the API how many past states (including the current) should
           be stored (minimum of 1, the current state). Note; too big of a number increases RAM usage!

        Examples
        --------

        Create a world builder and generate 10 worlds and run them:
        >>> from matrx.world_builder import WorldBuilder
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> for gridworld in builder.worlds():
        >>>     gridworld.run()

        Every `gridworld` received from builder.worlds() is a GridWorld instance.

        """

        # Only initialize when we did not already do so
        if not self.__is_initialized:
            # We update the grid, which fills everything with added objects and agents
            self.__update_grid()

            for agent_body in self.__registered_agents.values():
                agent_body.brain_initialize_func()

            # set the api variables
            self.__api_info = api_info
            self.__run_matrx_api = self.__api_info['run_matrx_api']
            if self.__run_matrx_api:
                # initialize this world in the api
                api.reset_api()
                api.tick_duration = self.__tick_duration
                api.register_world(self.world_id)
                api.current_tick = self.__current_nr_ticks
                api.grid_size = self.shape
                # point the api towards our message manager, for making messages available via the api
                api.gw_message_manager = self.message_manager
                api.gw = self
                api.teams = self.__teams
                if 'nr_states_to_store' in self.__api_info.keys():  # if not given, defaults to 5 in api.py (reset_api)
                    nr_states_to_store = max(self.__api_info['nr_states_to_store'], 1)
                    api.nr_states_to_store = nr_states_to_store

                # init api with world info
                api.MATRX_info = {
                    "nr_ticks": self.__current_nr_ticks,
                    "curr_tick_timestamp": int(round(time.time() * 1000)),
                    "grid_shape": self.__shape,
                    "tick_duration": self.tick_duration,
                    "world_ID": self.world_id,
                    "vis_settings": {
                        "vis_bg_clr": self.__visualization_bg_clr,
                        "vis_bg_img": self.__visualization_bg_img
                    }
                }
                # start paused
                api.matrx_paused = True

                # fetch the initial state of every agent to display
                self._fetch_initial_states()

            # Set initialisation boolean
            self.__is_initialized = True

            if self.__verbose:
                print(f"@{os.path.basename(__file__)}: Initialized the GridWorld.")

    def run(self, api_info):
        """ Runs the gridworld instance until stopped via the visualization or the goal has been achieved.

        The gridworld by default starts paused.

        Parameters
        ----------
        api_info : dictionary
          A dictionary which contians information on the API. At least containing the `api_thread` key with the
          API thread, and the `run_matrx_api` key which contains whether the GridWorld should start paused or not.

        Examples
        --------

        Create a world builder and generate 10 worlds and run them:
        >>> from matrx.world_builder import WorldBuilder
        >>> builder = WorldBuilder(shape=(10, 10))
        >>> for gridworld in builder.worlds():
        >>>     gridworld.run()

        """

        # initialize the gridworld
        self.initialize(api_info)

        if self.__verbose:
            print(f"@{os.path.basename(__file__)}: Starting game loop...")
        is_done = False
        while not is_done:

            if self.__run_matrx_api and api.matrx_paused:
                print("MATRX paused through api")
                gevent.sleep(1)
            else:
                is_done, tick_duration = self.__step()

            if self.__run_matrx_api and api.matrx_done:
                print("Scenario stopped through api")
                break

    def get_env_object(self, requested_id, obj_type=None):
        """ Fetch an object or agent from the GridWorld using its ID, optionally checking for its object type.

        Parameters
        ----------
        requested_id : dictionary
          The ID of the object or agent to fetch.

        obj_type : Class (optional, default, None)
          The object class of which the  object-to-fetch should be. Can be used as a filter: if the object with id
          `requested_id` is not of this class, it is not returned.

        Returns
        -------
        obj : Object or Agent
            Returns the object or agent with ID `requested_id` of tpe `obj_type` (if not None). If no object can be
            found that adheres to these filters, None is returned.

        Examples
        --------

        In an action, world goal, or somewhere else with access to the Gridworld, the function can be used as below.
        In this example the custom action removes a specific agent from the world when executed.

        >>> from matrx.agents import HumanAgent
        >>> class YourCustomAction(Action):
        >>>     def __init__(...):
        >>>         ...
        >>>
        >>>     def mutate(self, grid_world, agent_id, **kwargs):
        >>>         agent = grid_world.get_env_object("HumanAgent_23", HumanAgent)
        >>>         del agent

        Alternatively, if you know the object ID and type (object or agent) for certain, it can also be fetched
        as so:

        >>> reg_ag = grid_world.registered_agents[agent_id] # fetch agent by ID
        >>> env_obj = grid_world.environment_objects[object_id]  # fetch object by ID

        """

        obj = None

        # try to fetch object from agents
        if requested_id in self.__registered_agents.keys():
            if obj_type is not None:
                if isinstance(self.__registered_agents[requested_id], obj_type):
                    obj = self.__registered_agents[requested_id]
            else:
                obj = self.__registered_agents[requested_id]

        # try to fetch object from env objects
        if requested_id in self.__environment_objects.keys():
            if obj_type is not None:
                if isinstance(self.__environment_objects[requested_id], obj_type):
                    obj = self.__environment_objects[requested_id]
            else:
                obj = self.__environment_objects[requested_id]

        return obj

    def get_objects_in_range(self, agent_loc, object_type, sense_range):
        """ Get all objects of a specific obj type (normal objects or agent) within a certain range around an
        agent's location.

        Parameters
        ----------
        agent_loc : dictionary
          The location from which to search in a radius around for objects. Can be any [x,y] location within the
          GridWorld shape dimensions.

        obj_type : Class (optional, default, None)
          The object class of which the objects-to-find should be.

        sense_range : int
          The radius around the agent within which to look for objects.

        Returns
        -------
        obj : OrderedDict
            Returns an ordereddict with the objects and agents of tpe `object_type` within `sense_range` blocks of the
            location passed via `agent_loc`. If not objects were found, the ordered dict is empty.

        Examples
        --------

        In an action, world goal, or somewhere else with access to the Gridworld, the function can be used as
        below.
        In this example all objects of all types (denoted with the "*") within 5 tiles of the coordinate [3,3] are
        returned.

        >>> objects_in_range = grid_world.get_objects_in_range([3,3], object_type="*", sense_range=5)

        """

        env_objs = OrderedDict()
        # loop through all environment objects
        for obj_id, env_obj in self.__environment_objects.items():
            # get the distance from the agent location to the object
            coordinates = env_obj.location
            distance = get_distance(coordinates, agent_loc)

            # check if the env object is of the specified type, and within range
            if (object_type is None or object_type == "*" or isinstance(env_obj, object_type)) and \
                    distance <= sense_range:
                env_objs[obj_id] = env_obj

        # agents are also environment objects, but stored separably. Also check them.
        for agent_id, agent_obj in self.__registered_agents.items():
            coordinates = agent_obj.location
            distance = get_distance(coordinates, agent_loc)

            # check if the env object is of the specified type, adn within range
            if (object_type is None or object_type == "*" or isinstance(agent_obj, object_type)) and \
                    distance <= sense_range:
                env_objs[agent_id] = agent_obj
        return env_objs

    def remove_from_grid(self, object_id, remove_from_carrier=True):
        """ Remove an object from the grid.

        Parameters
        ----------
        object_id : int
          ID of the object to remove

        remove_from_carrier : Bool (optional, default, True)
          Whether to also remove from agents that are currently carrying the object.

        Returns
        -------
        obj : Bool
            Whether the object was sucessfully removed from the grid or not.

        Examples
        --------

        In an action, world goal, or somewhere else with access to the Gridworld, the function can be used as
        below.
        In this example the Agent3 is removed from the Grid.
        >>> succeeded = grid_world.remove_from_grid(object_id="Agent3", remove_from_carrier=False)

        In this example the object Block5 is removed from the Grid, and any Agents that were carrying it.
        >>> succeeded = grid_world.remove_from_grid(object_id="Block5", remove_from_carrier=True)

        """


        # Remove object first from grid
        grid_obj = self.get_env_object(object_id)  # get the object
        loc = grid_obj.location  # its location

        self.__grid[loc[1], loc[0]].remove(grid_obj.obj_id)  # remove the object id from the list at that location
        if len(self.__grid[loc[1], loc[0]]) == 0:  # if the list is empty, just add None there
            self.__grid[loc[1], loc[0]] = None

        # Remove object from the list of registered agents or environmental objects
        # Check if it is an agent
        if object_id in self.__registered_agents.keys():
            # Check if the agent was carrying something, if so remove property from carried item
            for obj_id in self.__registered_agents[object_id].is_carrying:
                self.__environment_objects[obj_id].carried_by.remove(object_id)

            # Remove agent
            success = self.__registered_agents.pop(object_id,
                                                   default=False)  # if it exists, we get it otherwise False

        # Else, check if it is an object
        elif object_id in self.__environment_objects.keys():
            # remove from any agents carrying this object if asked for
            if remove_from_carrier:
                # If the object was carried, remove this from the agent properties as well
                for agent_id in self.__environment_objects[object_id].carried_by:
                    obj = self.__environment_objects[object_id]
                    self.__registered_agents[agent_id].is_carrying.remove(obj)

            # Remove object
            success = self.__environment_objects.pop(object_id,
                                                     default=False)  # if it exists, we get it otherwise False
        else:
            success = False  # Object type not specified

        if success is not False:  # if succes is not false, we successfully removed the object from the grid
            success = True

        if self.__verbose:
            if success:
                print(f"@{os.path.basename(__file__)}: Succeeded in removing object with ID {object_id}")
            else:
                print(f"@{os.path.basename(__file__)}: Failed to remove object with ID {object_id}.")

        return success

    def _fetch_initial_states(self):
        """ MATRX starts paused by default, to prime the api and any connected GUI's, we fetch the first state
        from all agents to send which can be shown while waiting for the experiment leader to press play.
        """

        for agent_id, agent_obj in self.__registered_agents.items():
            # given the agent's capabilities, get everything the agent can perceive
            state = self.__get_agent_state(agent_obj)

            # filter other things from the agent state
            filtered_agent_state = agent_obj.filter_observations(state)

            # save the current agent's state for the api
            api.add_state(agent_id=agent_id, state=filtered_agent_state,
                          agent_inheritence_chain=agent_obj.class_inheritance,
                          world_settings=api.MATRX_info)

        # add god state
        api.add_state(agent_id="god", state=self.__get_complete_state(), agent_inheritence_chain="god",
                      world_settings=api.MATRX_info)

        # initialize the message manager
        self.message_manager.agents = self.__registered_agents.keys()
        self.message_manager.teams = self.__teams

        # make the information of this tick available via the api, after all
        # agents have been updated
        api.next_tick()

    def _register_agent(self, agent, agent_body: AgentBody):
        """ Register human agents and agents to the gridworld environment """

        # Random seed for agent between 1 and 10000000, might need to be adjusted still
        agent_seed = self.__rnd_gen.randint(1, 1000000)

        # check if the agent can be succesfully placed at that location
        self.__validate_obj_placement(agent_body)

        # Add agent to registered agents
        self.__registered_agents[agent_body.obj_id] = agent_body

        if self.__verbose:
            print(f"@{os.path.basename(__file__)}: Created agent with id {agent_body.obj_id}.")

        # Get all properties from the agent avatar
        avatar_props = agent_body.properties

        if agent_body.is_human_agent is False:
            agent._factory_initialise(agent_name=agent_body.obj_name,
                                      agent_id=agent_body.obj_id,
                                      action_set=agent_body.action_set,
                                      sense_capability=agent_body.sense_capability,
                                      agent_properties=avatar_props,
                                      customizable_properties=agent_body.customizable_properties,
                                      callback_is_action_possible=self.__check_action_is_possible,
                                      rnd_seed=agent_seed)
        else:  # if the agent is a human agent, we also assign its user input action map
            agent._factory_initialise(agent_name=agent_body.obj_name,
                                      agent_id=agent_body.obj_id,
                                      action_set=agent_body.action_set,
                                      sense_capability=agent_body.sense_capability,
                                      agent_properties=avatar_props,
                                      customizable_properties=agent_body.customizable_properties,
                                      callback_is_action_possible=self.__check_action_is_possible,
                                      rnd_seed=agent_seed,
                                      key_action_map=agent_body.properties["key_action_map"])

        return agent_body.obj_id

    def _register_env_object(self, env_object: EnvObject):
        """ this function adds the objects """

        # check if the object can be succesfully placed at that location
        self.__validate_obj_placement(env_object)

        # Assign id to environment sparse dictionary grid
        self.__environment_objects[env_object.obj_id] = env_object

        if self.__verbose:
            print(f"@{__file__}: Created an environment object with id {env_object.obj_id}.")

        return env_object.obj_id

    def _register_teams(self):
        """ Register all teams and who is in those teams.
        An agent is always in a team, if not set by the user, a team is created with name 'agent_id' with only that
        agent in it.
        """
        # loop through all agents
        for agent_id, agent_body in self.registered_agents.items():
            # find their team name
            team = agent_body.properties['team']

            # register the team (if not already done) and the agent in it
            if team not in self.__teams:
                self.__teams[team] = []
            self.__teams[team].append(agent_id)

    def _register_logger(self, logger: GridWorldLogger):
        if self.__loggers is None:
            self.__loggers = [logger]
        else:
            self.__loggers.append(logger)

    def __add_to_grid(self, grid_obj):

        if isinstance(grid_obj, EnvObject):
            loc = grid_obj.location
            if self.__grid[loc[1], loc[0]] is not None:
                self.__grid[loc[1], loc[0]].append(grid_obj.obj_id)
            else:
                self.__grid[loc[1], loc[0]] = [grid_obj.obj_id]
        else:
            raise BaseException(f"Object is not of type {str(type(EnvObject))} but of {str(type(grid_obj))} when adding"
                                f" to grid in GridWorld.")

    def __validate_obj_placement(self, env_object):
        """
        Checks whether an object can be successfully placed on the grid
        """
        obj_loc = env_object.location

        # get the objects at the target object location
        objs_at_loc = self.get_objects_in_range(obj_loc, "*", 0)

        # filter out areaTiles, which don't count
        for key in list(objs_at_loc.keys()):
            if AreaTile.__name__ in objs_at_loc[key].class_inheritance:
                objs_at_loc.pop(key)

        # check how many of these objects are intraversable
        intraversable_objs = []
        for obj in objs_at_loc:
            if not objs_at_loc[obj].is_traversable:
                intraversable_objs.append(objs_at_loc[obj].obj_id)

        # two intraversable objects can't be at the same location
        if not env_object.is_traversable and len(intraversable_objs) > 0:
            raise Exception(f"Invalid placement. Could not place object {env_object.obj_id} in grid, location already "
                            f"occupied by intraversable object {intraversable_objs} at location {obj_loc}")

    def __step(self):

        # Set tick start of current tick
        start_time_current_tick = datetime.datetime.now()

        # Check if we are done based on our global goal assessment function
        self.__is_done, goal_status = self.__check_simulation_goal()

        # Log the data if we have any loggers
        for logger in self.__loggers:
            agent_data_dict = {}
            for agent_id, agent_body in self.__registered_agents.items():
                agent_data_dict[agent_id] = agent_body.get_log_data()

            logger._grid_world_log(grid_world=self, agent_data=agent_data_dict,
                                   last_tick=self.__is_done, goal_status=goal_status)

        # If this grid_world is done, we return immediately
        if self.__is_done:
            return self.__is_done, 0.

        # initialize a temporary dictionary in which all states of this tick
        # will be saved. After all agents have been updated, the new tick info
        # will be made accessible via the api.
        if self.__run_matrx_api:
            api.temp_state = {}

            # if this is the first tick, clear the placeholder states
            if self.__current_nr_ticks == 0:
                api.MATRX_info = {}
                api.next_tick_info = {}

        # Go over all agents, detect what each can detect, figure out what actions are possible and send these to
        # that agent. Then receive the action back and store the action in a buffer.
        # Also, update the local copy of the agent properties, and save the agent's state for the GUI.
        # Then go to the next agent.
        # This blocks until a response from the agent is received (hence a tick can take longer than self.tick_
        # duration!!)
        action_buffer = OrderedDict()
        for agent_id, agent_obj in self.__registered_agents.items():

            state = self.__get_agent_state(agent_obj)

            # check if this agent is busy performing an action , if so then also check if it as its last tick of waiting
            # because then we want to do that action. If not busy, call its get_action function.
            if agent_obj._check_agent_busy(curr_tick=self.__current_nr_ticks):

                # only do the filter observation method to be able to update the agent's state to the api
                filtered_agent_state = agent_obj.filter_observations(state)

                # save the current agent's state for the api
                if self.__run_matrx_api:
                    api.add_state(agent_id=agent_id, state=filtered_agent_state,
                                  agent_inheritence_chain=agent_obj.class_inheritance,
                                  world_settings=self.__get_complete_state()['World'])

            else:  # agent is not busy

                # Any received data from the api for this HumanAgent is send along to the get_action function
                if agent_obj.is_human_agent:
                    usrinp = None
                    if self.__run_matrx_api and agent_id in api.userinput:
                        usrinp = api.pop_userinput(agent_id)

                    filtered_agent_state, agent_properties, action_class_name, action_kwargs = \
                        agent_obj.get_action_func(state=state, agent_properties=agent_obj.properties, agent_id=agent_id,
                                                  user_input=usrinp)
                else:  # not a HumanAgent

                    # perform the agent's get_action method (goes through filter_observations and decide_on_action)
                    filtered_agent_state, agent_properties, action_class_name, action_kwargs = agent_obj.get_action_func(
                        state=state, agent_properties=agent_obj.properties, agent_id=agent_id)

                # the Agent (in the OODA loop) might have updated its properties, process these changes in the Avatar
                # Agent
                agent_obj._set_agent_changed_properties(agent_properties)

                # Set the agent to busy, we do this only here and not when the agent was already busy to prevent the
                # agent to perform an action with a duration indefinitely (and since all actions have a duration, that
                # would be killing...)
                self.__set_agent_busy(action_name=action_class_name, action_kwargs=action_kwargs, agent_id=agent_id)

                # Get all agents we have, as we need these to process all messages that are send to all agents
                all_agent_ids = self.__registered_agents.keys()

                # Obtain all communication messages if the agent has something to say to others (only comes here when
                # the agent is NOT busy)
                agent_messages = agent_obj.get_messages_func(all_agent_ids)

                # add any messages received from the api sent by this agent
                if self.__run_matrx_api:
                    if agent_id in api.received_messages:
                        agent_messages += copy.copy(api.received_messages[agent_id])

                        # clear the messages for the next tick
                        del api.received_messages[agent_id]

                # preprocess all messages of the current tick of this agent
                self.message_manager.preprocess_messages(self.__current_nr_ticks, agent_messages,
                                                         all_agent_ids, self.__teams)

            # save the current agent's state for the api
            if self.__run_matrx_api:
                api.add_state(agent_id=agent_id, state=filtered_agent_state,
                              agent_inheritence_chain=agent_obj.class_inheritance,
                              world_settings=self.__get_complete_state()['World'])

            # if this agent is at its last tick of waiting on its action duration, we want to actually perform the
            # action
            if agent_obj._at_last_action_duration_tick(curr_tick=self.__current_nr_ticks):
                # Get the action and arguments
                action_class_name, action_kwargs = agent_obj._get_duration_action()
                # store the action in the buffer
                action_buffer[agent_id] = (action_class_name, action_kwargs)

        # put all messages of the current tick in the message buffer
        if self.__current_nr_ticks in self.message_manager.preprocessed_messages:
            for mssg in self.message_manager.preprocessed_messages[self.__current_nr_ticks]:
                if mssg.to_id not in self.__message_buffer.keys():  # first message for this receiver
                    self.__message_buffer[mssg.to_id] = [mssg]
                else:
                    self.__message_buffer[mssg.to_id].append(mssg)

        # save the god view state
        if self.__run_matrx_api:
            api.add_state(agent_id="god", state=self.__get_complete_state(), agent_inheritence_chain="god",
                          world_settings=self.__get_complete_state()['World'])

            # make the information of this tick available via the api, after all
            # agents have been updated
            api.current_tick = self.__current_nr_ticks
            api.next_tick()
            self.__tick_duration = api.tick_duration
            api.grid_size = self.shape

        # Perform the actions in the order of the action_buffer (which is filled in order of registered agents
        for agent_id, action in action_buffer.items():
            # Get the action class name
            action_class_name = action[0]
            # Get optional kwargs
            action_kwargs = action[1]

            if action_kwargs is None:  # If kwargs is none, make an empty dict out of it
                action_kwargs = {}

            # Actually perform the action (if possible), also sets the result in the agent's brain
            self.__perform_action(agent_id, action_class_name, action_kwargs)

            # Update the grid
            self.__update_grid()

        # Send all messages between agents
        for receiver_id, messages in self.__message_buffer.items():
            # check if the receiver exists
            if receiver_id in self.__registered_agents.keys():
                # Call the callback method that sets the messages
                self.__registered_agents[receiver_id].set_messages_func(messages)

        self.__message_buffer = {}

        # Perform the update method of all objects
        for env_obj in self.__environment_objects.values():
            env_obj.update(self)

        # Increment the number of tick we performed
        self.__current_nr_ticks += 1

        # Check how much time the tick lasted already
        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - start_time_current_tick
        self.sleep_duration = self.__tick_duration - tick_duration.total_seconds()

        # Sleep for the remaining time of self.__tick_duration
        self.__sleep()

        # Compute the total time of our tick (including potential sleep)
        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - start_time_current_tick
        self.__curr_tick_duration = tick_duration.total_seconds()

        if self.__verbose:
            print(f"@{os.path.basename(__file__)}: Tick {self.__current_nr_ticks} took {tick_duration.total_seconds()} "
                  f"seconds.")

        return self.__is_done, self.__curr_tick_duration

    def __check_simulation_goal(self):

        goal_status = {}
        if self.__simulation_goal is not None:
            if isinstance(self.__simulation_goal, (list, tuple)):  # edited this check to include tuples
                for sim_goal in self.__simulation_goal:
                    is_done = sim_goal.goal_reached(self)
                    goal_status[sim_goal] = is_done
            else:
                is_done = self.__simulation_goal.goal_reached(self)
                goal_status[self.__simulation_goal] = is_done

        is_done = np.array(list(goal_status.values())).all()
        return is_done, goal_status

    def __sleep(self):
        """
        Sleeps the current python process for the amount of time that is left after self.curr_tick_duration up to
        in self.__tick_duration
        :return:
        """
        if self.sleep_duration > 0:
            gevent.sleep(self.sleep_duration)
        else:
            self.__warn(
                f"The average tick took longer than the set tick duration of {self.__tick_duration}. "
                f"Program is to heavy to run real time")

    def __update_grid(self):
        self.__grid = np.array([[None for _ in range(self.__shape[0])] for _ in range(self.__shape[1])])
        for obj_id, obj in self.__environment_objects.items():
            self.__add_to_grid(obj)
        for agent_id, agent in self.__registered_agents.items():
            self.__add_to_grid(agent)

    # get all objects and agents on the grid
    def __get_complete_state(self):
        """
        Compile all objects and agents on the grid in one state dictionary
        :return: state with all objects and agents on the grid
        """

        # create a state with all objects and agents
        state = {}
        for obj_id, obj in self.__environment_objects.items():
            state[obj.obj_id] = obj.properties
        for agent_id, agent in self.__registered_agents.items():
            state[agent.obj_id] = agent.properties

        # Append generic properties (e.g. number of ticks, size of grid, etc.}
        state["World"] = {
            "nr_ticks": self.__current_nr_ticks,
            "curr_tick_timestamp": int(round(time.time() * 1000)),
            "grid_shape": self.__shape,
            "tick_duration": self.tick_duration,
            "world_ID": self.world_id,
            "vis_settings": {
                "vis_bg_clr": self.__visualization_bg_clr,
                "vis_bg_img": self.__visualization_bg_img
            }
        }

        return state

    def __get_agent_state(self, agent_obj: AgentBody):
        agent_loc = agent_obj.location
        sense_capabilities = agent_obj.sense_capability.get_capabilities()

        # Check if sense capabilities contains the "*" wildcard. If so we store
        # those objects separately, in case there are also other types specified
        # whose range precedes that of the "*" wildcard. For example, when an
        # agent can perceive other agents within a certain range and also has
        # the "*" wildcard to denote all OTHER objects. In that case we should
        # ignore all the AgentBody objects in the "*"-range. and then add all
        # the AgentBody objects we can see with the "AgentBody"-range.
        wildcard_objs = {}
        objs_in_range = OrderedDict()
        if "*" in sense_capabilities.keys():
            wildcard_objs = self.get_objects_in_range(agent_loc, "*", sense_capabilities["*"])
            sense_capabilities.pop("*")  # we did the wildcard already

        # Check which objects can be sensed with the agents' capabilities, from
        # its current position.
        for obj_type, sense_range in sense_capabilities.items():
            env_objs = self.get_objects_in_range(agent_loc, obj_type, sense_range)
            objs_in_range.update(env_objs)

        # Merge the wildcard objects with those of the (potential) other objects,
        # where we ignore all wildcard objects that are of a specific given type
        # with its own range.
        for wildcard_obj_id, wildcard_obj in wildcard_objs.items():
            if type(wildcard_obj) not in sense_capabilities.keys():
                objs_in_range[wildcard_obj_id] = wildcard_obj

        state = {}
        # Save all properties of the sensed objects in a state dictionary
        for env_obj in objs_in_range:
            state[env_obj] = objs_in_range[env_obj].properties

        # Append generic properties (e.g. number of ticks, fellow team members, etc.}
        team_members = [agent_id for agent_id, other_agent in self.__registered_agents.items()
                        if agent_obj.team == other_agent.team]
        state["World"] = {
            "nr_ticks": self.__current_nr_ticks,
            "curr_tick_timestamp": int(round(time.time() * 1000)),
            "grid_shape": self.__shape,
            "tick_duration": self.tick_duration,
            "team_members": team_members,
            "world_ID": self.world_id,
            "vis_settings": {
                "vis_bg_clr": self.__visualization_bg_clr,
                "vis_bg_img": self.__visualization_bg_img
            }
        }

        return state

    def __check_action_is_possible(self, agent_id, action_name, action_kwargs):
        # If the action_name is None, the agent idles
        if action_name is None:
            result = ActionResult(ActionResult.IDLE_ACTION, succeeded=True)
            return result

        # Check if the agent still exists (you would only get here if the agent is removed during this tick).
        if agent_id not in self.__registered_agents.keys():
            result = ActionResult(ActionResult.AGENT_WAS_REMOVED.replace("{AGENT_ID}", agent_id), succeeded=False)
            return result

        if action_name is None:  # If action is None, we send an action result that no action was given (and succeeded)
            result = ActionResult(ActionResult.NO_ACTION_GIVEN, succeeded=True)

        # action known, but agent not capable of performing it
        elif action_name in self.__all_actions.keys() and \
                action_name not in self.__registered_agents[agent_id].action_set:
            result = ActionResult(ActionResult.AGENT_NOT_CAPABLE, succeeded=False)

        # Check if action is known
        elif action_name in self.__all_actions.keys():
            # Get action class
            action_class = self.__all_actions[action_name]
            # Make instance of action
            action = action_class()
            # Check if action is possible, if so we can perform the action otherwise we send an ActionResult that it was
            # not possible.
            result = action.is_possible(self, agent_id, **action_kwargs)

        else:  # If the action is not known
            warnings.warn(f"The action with name {action_name} was not found when checking whether this action is "
                          f"possible to perform by agent {agent_id}.")
            result = ActionResult(ActionResult.UNKNOWN_ACTION, succeeded=False)

        return result

    def __perform_action(self, agent_id, action_name, action_kwargs):

        # Check if the action will succeed
        result = self.__check_action_is_possible(agent_id, action_name, action_kwargs)

        # If it will succeed, perform it.
        if result.succeeded:

            # If the action is None, nothing has to change in the world
            if action_name is None:
                return result

            # Get action class
            action_class = self.__all_actions[action_name]
            # Make instance of action
            action = action_class()
            # Apply world mutation
            result = action.mutate(self, agent_id, **action_kwargs)

            # Get agent's send_result function
            set_action_result = self.__registered_agents[agent_id].set_action_result_func
            # Send result of mutation to agent
            set_action_result(result)

            # Update the grid
            self.__update_agent_location(agent_id)

        # Whether the action succeeded or not, we return the result
        return result

    def __set_agent_busy(self, action_name, action_kwargs, agent_id):

        # Check if the action_name is None, in which case we simply idle for one tick
        if action_name is None:
            duration_in_ticks = 0

        else:  # action is not None

            # Get action class
            action_class = self.__all_actions[action_name]
            # Make instance of action
            action = action_class()

            # Obtain the duration of the action, defaults to the one of the action class if not in action_kwargs, and
            # otherwise that of Action
            duration_in_ticks = action.duration_in_ticks
            if "action_duration" in action_kwargs.keys():
                duration_in_ticks = action_kwargs["action_duration"]

            # Older kwarg name, raises deprecation warning
            if "duration_in_ticks" in action_kwargs.keys():
                warnings.warn("'duration_in_ticks' is deprecated for setting an action's duration; use "
                              "'action_duration'.", PendingDeprecationWarning)
                duration_in_ticks = action_kwargs["duration_in_ticks"]

        # The agent is now busy performing this action
        self.__registered_agents[agent_id]._set_agent_busy(curr_tick=self.current_nr_ticks,
                                                           action_duration=duration_in_ticks)

        # Set the action and result in the agent so we know where the agent is busy with. In addition this is appended
        # to its properties so others know what agent did)
        self.__registered_agents[agent_id]._set_current_action(action_name=action_name, action_args=action_kwargs)

    def __update_agent_location(self, agent_id):
        # Get current location of the agent
        loc = self.__registered_agents[agent_id].location
        # Check if that spot in our list that represents the grid, is None or a list of other objects
        if self.__grid[loc[1], loc[0]] is not None:  # If not None, we append the agent id to it
            self.__grid[loc[1], loc[0]].append(agent_id)
        else:  # if none, we make a new list with the agent id in it.
            self.__grid[loc[1], loc[0]] = [agent_id]

        # Update the Agent Avatar's location as well
        self.__registered_agents[agent_id].location = loc

    def __update_obj_location(self, obj_id):
        loc = self.__environment_objects[obj_id].location
        if self.__grid[loc[1], loc[0]] is not None:
            self.__grid[loc[1], loc[0]].append(obj_id)
        else:
            self.__grid[loc[1], loc[0]] = [obj_id]

    def __warn(self, warn_str):
        return f"[@{self.__current_nr_ticks}] {warn_str}"


    @property
    def registered_agents(self):
        """Dict: Dictionary of all registered agents, keys are the IDs, values are the registered objects. """
        return self.__registered_agents

    @property
    def environment_objects(self):
        """Dict: Dictionary of all non-agent environment objects, keys are the IDs, values are the registered objects.
        """
        return self.__environment_objects

    @property
    def is_done(self):
        """Bool: Boolean that indicates whether the GridWorld is done: either stopped by the user or due to the goal
         having been achieved."""
        return self.__is_done

    @property
    def current_nr_ticks(self):
        """Int: Current tick at which the gridworld is. """
        return self.__current_nr_ticks

    @property
    def grid(self):
        """Numpy 2D array: Numpy array of shape x by y. Each grid[x,y] location contains a list with all
        object IDs of the objects at that location"""
        return self.__grid

    @property
    def shape(self):
        """list: [x,y] shape of the grid """
        return self.__shape

    @property
    def simulation_goal(self):
        """WorldGoal: The world goal of type WorldGoal, or a class that extends WorldGoal """
        return self.__simulation_goal

    @property
    def tick_duration(self):
        """float: the desired duration of one tick. The real tick_duration might be longer due to a large amount of
         processing that needs to be done each tick by one or multiple agents. """
        return self.__tick_duration
