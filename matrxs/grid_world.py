import datetime
import time
import os.path
import warnings
from collections import OrderedDict

from matrxs.actions.object_actions import *
from matrxs.utils.utils import get_all_classes
from matrxs.objects.simple_objects import AreaTile
from matrxs.visualization import server
from matrxs.visualization.visualizer import Visualizer
from matrxs.objects.env_object import EnvObject


class GridWorld:

    def __init__(self, shape, tick_duration=0.5, simulation_goal=5000, run_sail_api=True, run_visualization_server=True,
                 rnd_seed=1, visualization_bg_clr="#C2C2C2", visualization_bg_img=None, verbose=False):
        """
        Creates an instance of a GridWorld that acts as a discrete state machine for agents and objects.

        The GridWorld is the main class of MATRXS which is responsible of storing objects and running the game loop.
        The world is tracked through two dictionaries; one for the agents and one for objects. Each get a unique
        identifier assigned that function as its key. Their locations are stored in a 3D array, the 'grid'. This grid
        stores these locations by having the unique ID of each object on a certain x and y coordinate with the 3rd
        dimension allowing multiple objects on a single location.

        A single pass of the game loop is referred to as a 'tick', in this tick the world goes through these steps:
        1. Check if all simulations goals are met, if so we end the game loop.
        2. Update the visualisation (if running).
        3. Obtain the actions from each agent and perform them (in order in which they were added)
        4. Let all objects perform their updates (in order in which they were added)
        5. Sleep for an amount to make sure each tick takes at least `tick_duration` seconds.

        Obtaining the action from an agent is blocking, meaning that the tick might take a while if there are many
        agents or when they take a lot of time to make a decision. In addition all agents whose turn it is or are not
        busy performing an action that takes time are queried. All other agents are ignored.

        Parameters
        ----------
        shape: list, tuple
            The size of the grid as (width, height).
        tick_duration: float, optional
            The duration of a single tick in seconds. The GridWorld assures that all ticks will take atleast this long.
            Defaults to 0.5 seconds.
        simulation_goal: SimulationGoal, list, int, optional
            The simulation goal or goals of this GridWorld. Either a single SimulationGoal or a list of such goals. If
            set to an integer this will default to a simulation that runs that number of ticks and then terminates. If
            this integer is negative, it runs indefinitely. Defaults to 5000 ticks.
        run_sail_api: bool, optional
            Not yet implemented. Whether the API server should be started (if not already running). Defaults to True.
        run_visualization_server: bool, optional
            Whether the visualisation server should be started (if not already running). Defaults to True.
        rnd_seed: int, optional
            The random seed for this GridWorld. Should be a non-zero positive integer. From this seed, all random seeds
            for the AgentBrains are generated.
        visualization_bg_clr: str, optional
            The hexidecimal colour string for the visualisation background. Defaults to "#C2C2C2" (light grey).
        visualization_bg_img: str, optional
            The background image to be used by the visualisation of the grid. Defaults to None (no image).
        verbose: bool, optional
            Whether this GridWorld should run in verbose. Defaults to False.
        """
        ##################
        # Public variables
        ##################
        self.verbose = verbose  # Set whether we should print anything or not

        ####################
        # Property variables
        ####################
        self.__agent_bodies = OrderedDict()  # The dictionary of all existing agents in the GridWorld
        self.__environment_objects = OrderedDict()  # The dictionary of all existing objects in the GridWorld
        self.__shape = shape  # The width and height of the GridWorld
        self.__simulation_goal = simulation_goal  # The simulation goal, the simulation ends when this/these are reached
        self.__is_done = False  # Whether the simulation is done (goal(s) reached)
        self.__tick_duration = tick_duration  # How long each tick should take (process sleeps until that time is passed)
        self.__current_nr_ticks = 0  # The number of tick this GridWorld has ran already

        ###################
        # Private variables
        ###################
        self.__run_sail_api = run_sail_api  # Whether we should run the (SAIL) API
        self.__run_visualization_server = run_visualization_server  # Whether we should run the (Visualisation) API
        self.__visualisation_process = None  # placeholder for the visualisation server process
        self.__visualization_bg_clr = visualization_bg_clr  # The background color of the visualisation
        self.__visualization_bg_img = visualization_bg_img  # The background image of the visualisation

        # Get all actions within all currently imported files
        self.__all_actions = get_all_classes(Action, omit_super_class=True)

        # Initialise an empty grid, a simple 3D array with lists of ID's
        self.__grid = np.array([[None for _ in range(shape[0])] for _ in range(shape[1])])
        self.__rnd_seed = rnd_seed  # The random seed of this GridWorld
        self.__rnd_gen = np.random.RandomState(seed=self.__rnd_seed)  # The random state of this GridWorld
        self.__curr_tick_duration = 0.  # Duration of the current tick
        self.__visualizer = None  # Placeholder for the Visualizer class
        self.__is_initialized = False  # Whether this GridWorld is already initialized
        self.__message_buffer = {}  # dictionary of messages that need to be send to agents, with receiver ids as keys

    def initialize(self):
        """
        Initializes this GridWorld instance, including the visualisation if it should be running.

        Can be called separately from `GridWorld.run()` but is not required as that call also call this method when the
        world is not yet initialized.

        Returns
        -------
        None

        """
        # Only initialize when we did not already do so
        if not self.__is_initialized:

            # We update the grid, which fills everything with added objects and agents
            self.__update_grid()

            # Initialize all agents
            for agent_body in self.agent_bodies.values():
                agent_body.brain_initialize_func()

            # Start the visualisation server process if we need to
            started_visualisation = False  # tracks if the server is running successfully
            if self.__run_visualization_server and self.__visualisation_process is None:

                # Start the visualisation server
                started_visualisation = self.__start_visualisation_server()

            # Initialize the visualizer
            self.__visualizer = Visualizer(self.shape, self.__visualization_bg_clr, self.__visualization_bg_img,
                                           verbose=self.verbose, server_running=started_visualisation)

            # Visualize already
            self.__initial_visualisation()

            if self.verbose:
                print(f"@{os.path.basename(__file__)}: Initialized the GridWorld.")

    def run(self):
        """
        Start this GridWorld's game loop.

        In addition it initializes the GridWorld through `GridWorld.initialize()` if not already done so.

        Returns
        -------
        None

        Notes
        -----
        This call blocks the main thread. A GridWorld does not run in a separate thread.

        """
        self.initialize()

        if self.verbose:
            print(f"@{os.path.basename(__file__)}: Starting game loop...")

        is_done = False
        while not is_done:
            is_done, tick_duration = self.__step()

    def get_env_object(self, requested_id, object_class=None):
        """
        Obtains a EnvObject from this GridWorld.

        It looks for a certain object ID and returns the EnvObject instance with that ID. In addition you can specify
        a certain type which the object should have.

        Parameters
        ----------
        requested_id: str
            The ID of the EnvObject that should be returned.
        object_class: callable, optional
            The class this object should have. Can be used to make sure that the object that is returned belongs to a
            specific class.

        Returns
        -------
        EnvObject
            Returns the EnvObject with the given ID. Returns None if the object is not found.

        """
        obj = None

        if requested_id in self.agent_bodies.keys():
            if object_class is not None:
                if isinstance(self.agent_bodies[requested_id], object_class):
                    obj = self.agent_bodies[requested_id]
            else:
                obj = self.agent_bodies[requested_id]

        if requested_id in self.environment_objects.keys():
            if object_class is not None:
                if isinstance(self.environment_objects[requested_id], object_class):
                    obj = self.environment_objects[requested_id]
            else:
                obj = self.environment_objects[requested_id]

        return obj

    def get_objects_in_range(self, origin_location, detect_range, object_class=EnvObject):
        """
        Get all EnvObjects of a specified obj type within a given range around the the given location.

        Parameters
        ----------
        origin_location: tuple, list
            The x and y coordinate that acts as the origin.
        detect_range: float
            The range in which all objects will be returned with the given origin. Distance is measured in Euclidean/
            Manhattan distance.
        object_class: callable, optional
            The class all objects within the given range should have. Defaults to EnvObject (base class of all objects).

        Returns
        -------
        OrderedDict
            All environment objects found in the specified range with the given object. If `object_class` was given,
            only objects with that class are returned. Is empty if no objects were found. The keys are the object's
            unique IDs and the values the actual object instance. Since these are not copies, making any changes to
            these objects result in changes to them in the GridWorld.
        """

        env_objs = OrderedDict()
        # loop through all environment objects
        for obj_id, env_obj in self.environment_objects.items():
            # get the distance from the agent location to the object
            coordinates = env_obj.location
            distance = get_distance(coordinates, origin_location)

            # check if the env object is of the specified type, and within range
            if (object_class is None or object_class == "*" or isinstance(env_obj, object_class)) and \
                    distance <= detect_range:
                env_objs[obj_id] = env_obj

        # agents are also environment objects, but stored separably. Also check them.
        for agent_id, agent_obj in self.agent_bodies.items():
            coordinates = agent_obj.location
            distance = get_distance(coordinates, origin_location)

            # check if the env object is of the specified type, adn within range
            if (object_class is None or object_class == "*" or isinstance(agent_obj, object_class)) and \
                    distance <= detect_range:
                env_objs[agent_id] = agent_obj
        return env_objs

    def remove_from_grid(self, object_id, remove_from_carrier=True):
        """
        Removes an object from the GridWorld.

        Parameters
        ----------
        object_id: str
            The unique ID of the object to be removed. Can either be of an actual object or an Agent.
        remove_from_carrier: bool, optional
            Whether the object should also be removed from whoever might be carrying it. If set to False, the inventory
            of agents that carry EnvObjects will be ignored. Defaults to True.

        Returns
        -------
        bool
            True on successful deletion, otherwise False.
        """

        # Remove object first from grid
        grid_obj = self.get_env_object(object_id)  # get the object
        loc = grid_obj.location  # its location

        self.__grid[loc[1], loc[0]].remove(grid_obj.obj_id)  # remove the object id from the list at that location
        if len(self.__grid[loc[1], loc[0]]) == 0:  # if the list is empty, just add None there
            self.__grid[loc[1], loc[0]] = None

        # Remove object from the list of registered agents or environmental objects
        # Check if it is an agent
        if object_id in self.agent_bodies.keys():
            # Check if the agent was carrying something, if so remove property from carried item
            for obj_id in self.agent_bodies[object_id].is_carrying:
                self.environment_objects[obj_id].carried_by.remove(object_id)

            # Remove agent
            success = self.agent_bodies.pop(object_id,
                                            default=False)  # if it exists, we get it otherwise False

        # Else, check if it is an object
        elif object_id in self.environment_objects.keys():
            # remove from any agents carrying this object if asked for
            if remove_from_carrier:
                # If the object was carried, remove this from the agent properties as well
                for agent_id in self.environment_objects[object_id].carried_by:
                    obj = self.environment_objects[object_id]
                    self.agent_bodies[agent_id].is_carrying.remove(obj)

            # Remove object
            success = self.environment_objects.pop(object_id,
                                                   default=False)  # if it exists, we get it otherwise False
        else:
            success = False  # Object type not specified

        if success is not False:  # if succes is not false, we successfully removed the object from the grid
            success = True

        if self.verbose:
            if success:
                print(f"@{os.path.basename(__file__)}: Succeeded in removing object with ID {object_id}")
            else:
                print(f"@{os.path.basename(__file__)}: Failed to remove object with ID {object_id}.")

        return success

    def add_to_grid(self, grid_obj):
        """
        Adds an EnvObject instance to the grid.

        Parameters
        ----------
        grid_obj: EnvObject
            The object to add to the grid.

        Returns
        -------

        Raises
        ------
        IndexError
            When the x and/or y coordinate are out of bounds given the grid size.
        TypeError
            When the given object is not of type EnvObject (or inherits from it).
        """
        if isinstance(grid_obj, EnvObject):
            loc = grid_obj.location

            if 0 > loc[0] or loc[0] >= self.shape[0]:
                raise IndexError(f"The x coordinate of {loc} if out of bounds, should be between 0 and "
                                 f"{self.shape[0]}")
            if 0 > loc[1] or loc[1] >= self.shape[1]:
                raise IndexError(f"The y coordinate of {loc} if out of bounds, should be between 0 and "
                                 f"{self.shape[1]}")

            if self.__grid[loc[1], loc[0]] is not None:
                self.__grid[loc[1], loc[0]].append(grid_obj.obj_id)
            else:
                self.__grid[loc[1], loc[0]] = [grid_obj.obj_id]
        else:
            raise TypeError(f"The given object is of type {grid_obj.__class__.__name__} instead of type "
                            f"{EnvObject.__name__} or a child class of this.")

    @property
    def shape(self):
        """
        The width and height of this GridWorld.
        Returns
        -------
        tuple
            The (width, height).
        """
        return (self.__shape[0], self.__shape[1])

    @shape.setter
    def shape(self, _):
        warnings.warn("Trying to set the shape of a GridWorld. This should not be done after instance creation.")

    @property
    def agent_bodies(self):
        """
        An OrderedDictionary containing the AgentBody of each added agent.

        Returns
        -------
        OrderedDict
            The dictionary containing all added agents in order in which they were added with their IDs as keys.
        """
        return self.__agent_bodies

    @agent_bodies.setter
    def agent_bodies(self, _):
        warnings.warn("Trying to set the agent_bodies of a GridWorld. This should never be done, use the appropriate "
                      "public methods in GridWorld to change this dictionary.")

    @property
    def environment_objects(self):
        """
        An OrderedDictionary containing the EnvObject of each added object (excluding agents).

        Returns
        -------
        OrderedDict
            The dictionary containing all added objects in order in which they were added with their IDs as keys.
        """
        return self.__environment_objects

    @environment_objects.setter
    def environment_objects(self, _):
        warnings.warn("Trying to set the environment_objects of a GridWorld. This should never be done, use the "
                      "appropriate public methods in GridWorld to change this dictionary.")

    @property
    def simulation_goal(self):
        return self.__simulation_goal

    @simulation_goal.setter
    def simulation_goal(self, _):
        warnings.warn("Trying to set the simulation_goal of a GridWorld. This should not be done after instance "
                      "creation.")

    @property
    def is_done(self):
        return self.__is_done

    @property
    def tick_duration(self):
        return self.__tick_duration

    @tick_duration.setter
    def tick_duration(self, value):
        warnings.warn("Setting the tick_duration of a GridWorld after instance creation. This may result in undefined"
                      "behavior and is not test.")
        self.__tick_duration = value

    @property
    def current_nr_ticks(self):
        return self.__current_nr_ticks

    @property
    def grid(self):
        return self.__grid

    @grid.setter
    def grid(self, _):
        warnings.warn("Trying to set the grid of a GridWorld. This should not be done after instance creation.")

    def _add_agent(self, agent_brain, agent_avatar: AgentBody):
        """ Adds a single agent body and connects it with its brain. """

        # Random seed for agent between 1 and 10000000
        agent_seed = self.__rnd_gen.randint(1, 1000000)

        # check if the agent can be successfully placed at that location
        self.__validate_obj_placement(agent_avatar)

        # Add agent to the dict of agent bodies
        self.agent_bodies[agent_avatar.obj_id] = agent_avatar

        if self.verbose:
            print(f"@{os.path.basename(__file__)}: Created agent with id {agent_avatar.obj_id}.")

        # Get all properties from the agent avatar
        avatar_props = agent_avatar.properties

        if agent_avatar.is_human_agent is False:
            agent_brain._factory_initialise(agent_name=agent_avatar.obj_name,
                                            agent_id=agent_avatar.obj_id,
                                            action_set=agent_avatar.action_set,
                                            sense_capability=agent_avatar.sense_capability,
                                            agent_properties=avatar_props,
                                            customizable_properties=agent_avatar.customizable_properties,
                                            callback_is_action_possible=self.__check_action_is_possible,
                                            rnd_seed=agent_seed)
        else:  # if the agent is a human agent, we also assign its user input action map
            agent_brain._factory_initialise(agent_name=agent_avatar.obj_name,
                                            agent_id=agent_avatar.obj_id,
                                            action_set=agent_avatar.action_set,
                                            sense_capability=agent_avatar.sense_capability,
                                            agent_properties=avatar_props,
                                            customizable_properties=agent_avatar.customizable_properties,
                                            callback_is_action_possible=self.__check_action_is_possible,
                                            rnd_seed=agent_seed,
                                            usrinp_action_map=agent_avatar.properties["usrinp_action_map"])

        return agent_avatar.obj_id

    def _add_env_object(self, env_object: EnvObject):
        """ this function adds the objects """

        # check if the object can be succesfully placed at that location
        self.__validate_obj_placement(env_object)

        # Assign id to environment sparse dictionary grid
        self.environment_objects[env_object.obj_id] = env_object

        if self.verbose:
            print(f"@{__file__}: Created an environment object with id {env_object.obj_id}.")

        return env_object.obj_id

    def __step(self):

        # Check if we are done based on our global goal assessment function
        self.__is_done = self.__check_simulation_goal()

        # If this grid_world is done, we return immediately
        if self.__is_done:
            return self.__is_done, 0.

        # Set tick start of current tick
        start_time_current_tick = datetime.datetime.now()

        # Get all actions, filtered states and messages from all agents (not yet performed though)
        actions, messages, properties = self.__get_agent_actions()

        # Update the visualisation based on all the agents filtered states
        self.__update_visualisation()

        # Perform every action (in order of added agents)
        self.__update_grid_world(actions, properties)

        # Send all messages (in ordered of added agents, added messages)
        self.__send_all_messages(messages)

        # Perform the update on all objects
        self.__update_objects()

        # Handle tick duration
        self.__handle_tick_duration(start_time_current_tick)

        # Return our is_done boolean and current tick duration
        return self.__is_done, self.__curr_tick_duration

    def __get_agent_actions(self):
        # Variables to store the actions, potentially adjusted agent properties and messages to be send
        body_properties = OrderedDict()
        actions = OrderedDict()
        messages = OrderedDict()

        # Loop through each agent body
        for agent_id, agent_obj in self.agent_bodies.items():

            # Obtain the pre-filtered state for this agent
            state = self.__get_agent_state(agent_obj)

            # Check if the agent is busy with an action that takes time, if so we do not obtain its actions or messages
            # only its filtered state.
            if agent_obj._check_agent_busy(curr_tick=self.__current_nr_ticks):
                # Let the agent filter the state
                filtered_state = agent_obj.filter_observations(state)

            # If the current AgentBody is that of a HumanAgent any user inputs from the GUI for this HumanAgent are
            # send along in the state.
            elif agent_obj.is_human_agent:

                # If the HumanAgent received any user key input, we obtain this from the visualizer. Otherwise its None.
                if agent_id.lower() in self.__visualizer._user_inputs:
                    user_input = self.__visualizer._userinputs[agent_id.lower()]
                else:
                    user_input = None

                # Add the user input to the state dictionary
                state["user_inputs"] = user_input

                # Get the filtered_state, agent_properties, action_class and potential action_kwargs.
                filtered_state, properties, action_class_name, action_kwargs = agent_obj.get_action_func(
                    state=state, agent_properties=agent_obj.properties, agent_id=agent_id)

                # Obtain all communication messages if the agent has something to say to others
                messages = self.__append_agent_messages(agent_obj, messages)

                # Save the agent_properties, action_class and potential action_kwargs
                actions[agent_id] = (action_class_name, action_kwargs)
                body_properties[agent_id] = properties

            # If the current AgentBody is a regular agent we simply query it for its action based on the current pre-
            # filtered state.
            else:

                # Get the filtered_state, agent_properties, action_class and potential action_kwargs.
                filtered_state, properties, action_class_name, action_kwargs = agent_obj.get_action_func(
                    state=state, agent_properties=agent_obj.properties, agent_id=agent_id)

                # Obtain all communication messages if the agent has something to say to others
                messages = self.__append_agent_messages(agent_obj, messages)

                # Save the agent_properties, action_class and potential action_kwargs
                actions[agent_id] = (action_class_name, action_kwargs)
                body_properties[agent_id] = properties

            # Store the state in the Visualizer
            self.__visualizer._save_state(state=filtered_state, id=agent_id,
                                          inheritance_chain=agent_obj.class_inheritance)

        # Save the state of the god view in the visualizer
        self.__visualizer._save_state(inheritance_chain="god", id="god", state=self.__get_complete_state())

        return actions, messages, body_properties

    def __append_agent_messages(self, agent_obj, messages):
        agent_messages = agent_obj.get_messages_func()
        if len(agent_messages) > 0:  # there are messages
            # go through all messages
            for mssg in agent_messages:
                if mssg['to_id'] not in messages.keys():  # first message for this receiver
                    messages[mssg['to_id']] = [mssg]
                else:
                    messages[mssg['to_id']].append(mssg)

        return messages

    def __update_visualisation(self):
        # update the visualizations of all (human)agents and god
        self.__visualizer._update_guis(tick=self.__current_nr_ticks)

    def __update_grid_world(self, actions, properties):

        # Loop over all agents and its actions and properties (in order in which agents where added to the grid world,
        # excluding all agents that are still busy with an action or whose turn to act is not in this tick).
        for agent_id, action_data in actions.items():
            # Get the name of the action, its keyword arguments and its (potentially altered properties)
            action_name = action_data[0]
            action_kwargs = action_data[1]
            body_properties = properties[agent_id]

            # If kwargs is none, make an empty dict out of it
            if action_kwargs is None:
                action_kwargs = {}

            # Change the properties in the agent's body (if allowed to)
            self.agent_bodies[agent_id]._set_agent_changed_properties(body_properties)

            # Actually perform the action (if possible), also sets the result in the agent's brain
            self.__perform_action(agent_id, action_name, action_kwargs)

            # Update the grid
            self.__update_grid()

    def __send_all_messages(self, all_messages):
        # Send all messages between agents
        for receiver_id, messages in all_messages.items():

            # check if the receiver exists
            if receiver_id in self.agent_bodies.keys():
                # Call the callback method that sets the messages
                self.agent_bodies[receiver_id].set_messages_func(messages)

            # If the receiver is None, we send it to ALL agents.
            elif receiver_id is None:
                for agent_id in self.agent_bodies.keys():
                    # Call the callback method that sets the messages
                    self.agent_bodies[agent_id].set_messages_func(messages)

    def __update_objects(self):
        # Perform the update method of all objects
        for env_obj in self.environment_objects.values():
            env_obj.update(self)

    def __handle_tick_duration(self, tick_start_time):

        # Increment the number of tick we performed
        self.__current_nr_ticks += 1

        # Check how much time the tick lasted already
        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time
        self.sleep_duration = self.__tick_duration - tick_duration.total_seconds()

        # Sleep for the remaining time of self.tick_duration
        self.__sleep()

        # Compute the total time of our tick (including potential sleep)
        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time
        self.__curr_tick_duration = tick_duration.total_seconds()

        if self.verbose:
            print(f"@{os.path.basename(__file__)}: Tick {self.__current_nr_ticks} took {tick_duration.total_seconds()} "
                  f"seconds.")

    def __validate_obj_placement(self, env_object):
        """ Checks whether an object can be successfully placed on the grid """

        obj_loc = env_object.location

        # get the objects at the target object location
        objs_at_loc = self.get_objects_in_range(origin_location=obj_loc, detect_range=0)

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

    def __check_simulation_goal(self):
        """ Checks the simulation goal(s) """

        if self.__simulation_goal is not None:
            if isinstance(self.__simulation_goal, list):
                for sim_goal in self.__simulation_goal:
                    is_done = sim_goal.goal_reached(self)
                    if is_done is False:
                        return False
            else:
                return self.__simulation_goal.goal_reached(self)

        return False

    def __sleep(self):
        """
        Sleeps the current python process for the amount of time that is left after self.curr_tick_duration up to
        in self.tick_duration
        :return:
        """
        if self.sleep_duration > 0:
            time.sleep(self.sleep_duration)
        else:
            self.__warn(
                f"The average tick took longer than the set tick duration of {self.__tick_duration}. "
                f"Program is to heavy to run real time")

    def __update_grid(self):
        """ Clear the current grid and creats a new one with all currently known objects """

        self.__grid = np.array([[None for _ in range(self.shape[0])] for _ in range(self.shape[1])])
        for obj_id, obj in self.environment_objects.items():
            self.add_to_grid(obj)
        for agent_id, agent in self.agent_bodies.items():
            self.add_to_grid(agent)

    def __get_complete_state(self):
        """
        Compile all objects and agents on the grid in one state dictionary
        :return: state with all objects and agents on the grid
        """

        # create a state with all objects and agents
        perceived_objects = {}
        for obj_id, obj in self.environment_objects.items():
            perceived_objects[obj.obj_id] = obj.properties
        for agent_id, agent in self.agent_bodies.items():
            perceived_objects[agent.obj_id] = agent.properties

        # Make sure we comply with the structure of a 'state' dictionary
        state = {
            "world":
                {
                    "nr_ticks": self.__current_nr_ticks,
                    "grid_shape": self.shape
                },
            "internal_state": {},
            "perceived_objects": perceived_objects
        }

        return state

    def __get_agent_state(self, agent_obj: AgentBody):
        agent_loc = agent_obj.location
        sense_capabilities = agent_obj.sense_capability.get_capabilities()
        objs_in_range = OrderedDict()

        # Check which objects can be sensed with the agents' capabilities, from
        # its current position.
        for obj_type, sense_range in sense_capabilities.items():
            env_objs = self.get_objects_in_range(origin_location=agent_loc, detect_range=sense_range,
                                                 object_class=obj_type)
            objs_in_range.update(env_objs)

        # Save all properties of the sensed objects in a state dictionary
        perceived_objects = {}
        for object_key in objs_in_range:
            perceived_objects[object_key] = objs_in_range[object_key].properties

        # Append generic properties (e.g. number of ticks, fellow team members, etc.}
        team_members = [agent_id for agent_id, other_agent in self.agent_bodies.items()
                        if agent_obj.team == other_agent.team]

        # Get internal state and remove it from the perceived objects
        internal_state = perceived_objects[agent_obj.obj_id]

        state = {
            "world":
            {
                "nr_ticks": self.__current_nr_ticks,
                "grid_shape": self.shape,
                "team_members": team_members
            },
            "internal_state": internal_state,
            "perceived_objects": perceived_objects
        }

        return state

    def __check_action_is_possible(self, agent_id, action_name, action_kwargs):
        # If the action_name is None, the agent idles
        if action_name is None:
            result = ActionResult(ActionResult.IDLE_ACTION, succeeded=True)
            return result

        # Check if the agent still exists (you would only get here if the agent is removed during this tick).
        if agent_id not in self.agent_bodies.keys():
            result = ActionResult(ActionResult.AGENT_WAS_REMOVED.replace("{AGENT_ID}", agent_id), succeeded=False)
            return result

        if action_name is None:  # If action is None, we send an action result that no action was given (and succeeded)
            result = ActionResult(ActionResult.NO_ACTION_GIVEN, succeeded=True)

        # action known, but agent not capable of performing it
        elif action_name in self.__all_actions.keys() and \
                action_name not in self.agent_bodies[agent_id].action_set:
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

            # Obtain the duration of the action, defaults to the one of the action class if not in action_kwargs, and
            # otherwise that of Action
            duration_in_ticks = action.duration_in_ticks
            if "duration_in_ticks" in action_kwargs.keys():
                duration_in_ticks = action_kwargs["duration_in_ticks"]

            # The agent is now busy performing this action
            self.agent_bodies[agent_id]._set_agent_busy(curr_tick=self.__current_nr_ticks,
                                                        action_duration=duration_in_ticks)

            # Get agent's send_result function
            set_action_result = self.agent_bodies[agent_id].set_action_result_func
            # Send result of mutation to agent
            set_action_result(result)

            # Update the grid
            self.__update_agent_location(agent_id)

        # Whether the action succeeded or not, we return the result
        return result

    def __update_agent_location(self, agent_id):
        # Get current location of the agent
        loc = self.agent_bodies[agent_id].location
        # Check if that spot in our list that represents the grid, is None or a list of other objects
        if self.__grid[loc[1], loc[0]] is not None:  # If not None, we append the agent id to it
            self.__grid[loc[1], loc[0]].append(agent_id)
        else:  # if none, we make a new list with the agent id in it.
            self.__grid[loc[1], loc[0]] = [agent_id]

        # Update the Agent Avatar's location as well
        self.agent_bodies[agent_id].location = loc

    def __update_obj_location(self, obj_id):
        loc = self.environment_objects[obj_id].location
        if self.__grid[loc[1], loc[0]] is not None:
            self.__grid[loc[1], loc[0]].append(obj_id)
        else:
            self.__grid[loc[1], loc[0]] = [obj_id]

    def __warn(self, warn_str):
        return f"[@{self.__current_nr_ticks}] {warn_str}"

    def __initial_visualisation(self):

        # Perform the initiali visualisation of the process is set and the boolean for running it is true
        if self.__run_visualization_server and self.__visualisation_process is None:
            # Loop through all agents, apply their observe to get their state for the gui
            for agent_id, agent_obj in self.agent_bodies.items():
                # TODO the agent's filtered state is now empty as it has not yet performed an action. Fill it or forget
                # TODO about initializing the agent views?
                # Obtain the agent's filtered state
                filtered_agent_state = agent_obj.get_filtered_state()
                # Save the state
                self.__visualizer._save_state(inheritance_chain=agent_obj.class_inheritance, id=agent_id,
                                              state=filtered_agent_state)

            # save the state of the god view in the visualizer
            self.__visualizer._save_state(inheritance_chain="god", id="god", state=self.__get_complete_state())

            # update the visualizations of all (human)agents and god
            self.__visualizer._update_guis(tick=self.__current_nr_ticks)

    def __start_visualisation_server(self):
        # bool to denote whether we succeeded in starting the visualisation server
        succeeded = True

        # Set the server to debug mode if we are verbose
        # TODO Enable this when the debugging of the visualisation is correct (see issue #124)
        # server.debug = self.__verbose

        # Create the process and run it
        server.run_visualisation_server()
        self.__visualisation_process = True

        return succeeded
