import datetime
import os.path
import warnings
import gevent
from collections import OrderedDict
import time
import copy

from matrxs.logger.logger import GridWorldLogger
from matrxs.actions.object_actions import *
from matrxs.utils.utils import get_all_classes
from matrxs.objects.simple_objects import AreaTile
from visualization import server
from visualization.visualizer import Visualizer
from matrxs.objects.env_object import EnvObject
from matrxs.API import api
from matrxs.agents.agent_brain import AgentBrain


class GridWorld:

    def __init__(self, shape, tick_duration, simulation_goal, run_matrxs_api=True, run_visualization_server=True,
                 rnd_seed=1, visualization_bg_clr="#C2C2C2", visualization_bg_img=None, verbose=False):
        self.__tick_duration = tick_duration  # How long each tick should take (process sleeps until thatr time is passed)
        self.__simulation_goal = simulation_goal  # The simulation goal, the simulation end when this/these are reached
        self.__shape = shape  # The width and height of the GridWorld
        self.__run_matrxs_api = run_matrxs_api  # Whether we should run the MATRXS API
        self.__run_visualization_server = run_visualization_server  # Whether we should run the visualization server
        self.__visualisation_process = None  # placeholder for the visualisation server process
        self.__api_process = None # placeholder for the API server process
        self.__visualization_bg_clr = visualization_bg_clr  # The background color of the visualisation
        self.__visualization_bg_img = visualization_bg_img  # The background image of the visualisation
        self.__verbose = verbose  # Set whether we should print anything or not

        self.__registered_agents = OrderedDict()  # The dictionary of all existing agents in the GridWorld
        self.__environment_objects = OrderedDict()  # The dictionary of all existing objects in the GridWorld

        # Get all actions within all currently imported files
        self.__all_actions = get_all_classes(Action, omit_super_class=True)

        # Initialise an empty grid, a simple 2D array with ID's
        self.__grid = np.array([[None for _ in range(shape[0])] for _ in range(shape[1])])

        self.__loggers = []  # a list of GridWorldLogger use to log the data
        self.__is_done = False  # Whether the simulation is done (goal(s) reached)
        self.__rnd_seed = rnd_seed  # The random seed of this GridWorld
        self.__rnd_gen = np.random.RandomState(seed=self.__rnd_seed)  # The random state of this GridWorld
        self.__curr_tick_duration = 0.  # Duration of the current tick
        self.__current_nr_ticks = 0  # The number of tick this GridWorld has ran already
        self.__visualizer = None  # Placeholder for the Visualizer class
        self.__is_initialized = False  # Whether this GridWorld is already initialized
        self.__message_buffer = {}  # dictionary of messages that need to be send to agents, with receiver ids as keys

    def initialize(self):
        # Only initialize when we did not already do so
        if not self.__is_initialized:

            # We update the grid, which fills everything with added objects and agents
            self.__update_grid()

            for agent_body in self.__registered_agents.values():
                agent_body.brain_initialize_func()

            # reset the API variables
            if self.__run_matrxs_api:
                api.reset_api()
                api.tick_duration = self.__tick_duration


            # Start the visualisation server process if we need to
            # started_visualisation = False  # tracks if the server is running successfully
            # if self.__run_visualization_server and self.__visualisation_process is None:
            #     # Start the visualisation server
            #     started_visualisation = self.__start_visualisation_server()
            #
            # # Initialize the visualizer
            # self.__visualizer = Visualizer(self.__shape, self.__visualization_bg_clr, self.__visualization_bg_img,
            #                                verbose=self.__verbose, server_running=started_visualisation)

            # Visualize already
            # self.__initial_visualisation()

            # thread = threading.Thread(target=logMatrx.log_object_complete, args=(self,))
            # thread.start()


            # start the MATRXS API server if we need to
            started_API = False
            if self.__run_matrxs_api and self.__api_process is None:
                # start the MATRXS API server
                started_API = self.__start_API()
                # make a function available to the API for adding agent messages
                api.add_message_to_agent = self.add_API_message_to_agent

            # Set initialisation boolean
            self.__is_initialized = True

            if self.__verbose:
                print(f"@{os.path.basename(__file__)}: Initialized the GridWorld.")

    def run(self):
        self.initialize()

        if self.__verbose:
            print(f"@{os.path.basename(__file__)}: Starting game loop...")
        is_done = False
        while not is_done:

            if self.__run_matrxs_api and api.matrxs_paused:
                print("MATRXS paused through API")
                gevent.sleep(1)
            else:
                is_done, tick_duration = self.__step()

            if self.__run_matrxs_api and api.matrxs_done:
                print("Scenario stopped through API")
                break



    def get_env_object(self, requested_id, obj_type=None):
        obj = None

        if requested_id in self.__registered_agents.keys():
            if obj_type is not None:
                if isinstance(self.__registered_agents[requested_id], obj_type):
                    obj = self.__registered_agents[requested_id]
            else:
                obj = self.__registered_agents[requested_id]

        if requested_id in self.__environment_objects.keys():
            if obj_type is not None:
                if isinstance(self.__environment_objects[requested_id], obj_type):
                    obj = self.__environment_objects[requested_id]
            else:
                obj = self.__environment_objects[requested_id]

        return obj

    def get_objects_in_range(self, agent_loc, object_type, sense_range):
        """
        Get all objects of a obj type (normal objects or agent) within a
        certain range around the agent's location
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
        """
        Remove an object from the grid
        :param object_id: ID of the object to remove
        :param remove_from_carrier: whether to also remove from agents which carry the
        object or not.
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

    def add_to_grid(self, grid_obj):
        if isinstance(grid_obj, EnvObject):
            loc = grid_obj.location
            if self.__grid[loc[1], loc[0]] is not None:
                self.__grid[loc[1], loc[0]].append(grid_obj.obj_id)
            else:
                self.__grid[loc[1], loc[0]] = [grid_obj.obj_id]
        else:
            loc = grid_obj.location
            if self.__grid[loc[1], loc[0]] is not None:
                self.__grid[loc[1], loc[0]].append(grid_obj.obj_id)
            else:
                self.__grid[loc[1], loc[0]] = [grid_obj.obj_id]

    def _register_agent(self, agent, agent_avatar: AgentBody):
        """ Register human agents and agents to the gridworld environment """

        # Random seed for agent between 1 and 10000000, might need to be adjusted still
        agent_seed = self.__rnd_gen.randint(1, 1000000)

        # check if the agent can be succesfully placed at that location
        self.__validate_obj_placement(agent_avatar)

        # Add agent to registered agents
        self.__registered_agents[agent_avatar.obj_id] = agent_avatar

        if self.__verbose:
            print(f"@{os.path.basename(__file__)}: Created agent with id {agent_avatar.obj_id}.")

        # Get all properties from the agent avatar
        avatar_props = agent_avatar.properties

        if agent_avatar.is_human_agent is False:
            agent._factory_initialise(agent_name=agent_avatar.obj_name,
                                      agent_id=agent_avatar.obj_id,
                                      action_set=agent_avatar.action_set,
                                      sense_capability=agent_avatar.sense_capability,
                                      agent_properties=avatar_props,
                                      customizable_properties=agent_avatar.customizable_properties,
                                      callback_is_action_possible=self.__check_action_is_possible,
                                      rnd_seed=agent_seed)
        else:  # if the agent is a human agent, we also assign its user input action map
            agent._factory_initialise(agent_name=agent_avatar.obj_name,
                                      agent_id=agent_avatar.obj_id,
                                      action_set=agent_avatar.action_set,
                                      sense_capability=agent_avatar.sense_capability,
                                      agent_properties=avatar_props,
                                      customizable_properties=agent_avatar.customizable_properties,
                                      callback_is_action_possible=self.__check_action_is_possible,
                                      rnd_seed=agent_seed,
                                      key_action_map=agent_avatar.properties["key_action_map"])

        return agent_avatar.obj_id

    def _register_env_object(self, env_object: EnvObject):
        """ this function adds the objects """

        # check if the object can be succesfully placed at that location
        self.__validate_obj_placement(env_object)

        # Assign id to environment sparse dictionary grid
        self.__environment_objects[env_object.obj_id] = env_object

        if self.__verbose:
            print(f"@{__file__}: Created an environment object with id {env_object.obj_id}.")

        return env_object.obj_id

    def _register_logger(self, logger: GridWorldLogger):
        if self.__loggers is None:
            self.__loggers = [logger]
        else:
            self.__loggers.append(logger)

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
        # will be made accessible via the API.
        if self.__run_matrxs_api:
            api.temp_state = {}

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

                # only do the filter observation method to be able to update the agent's state to the API
                filtered_agent_state = agent_obj.filter_observations(state)

                # save the current agent's state for the visualizer
                if self.__run_matrxs_api:
                    api.add_state(agent_id=agent_id, state=filtered_agent_state, agent_inheritence_chain=agent_obj.class_inheritance)

                # if this busy agent is at its last tick of waiting, we want to actually perform the action
                if agent_obj._at_last_action_duration_tick(curr_tick=self.__current_nr_ticks):
                    action_class_name, action_kwargs = agent_obj._get_duration_action()

                    # store the action in the buffer
                    action_buffer[agent_id] = (action_class_name, action_kwargs)

            else:  # agent is not busy

                # For a HumanAgent any received data from the API for this HumanAgent is send along
                if agent_obj.is_human_agent:
                    usrinp = None
                    if self.__run_matrxs_api and agent_id in api.userinput:
                        usrinp = api.pop_userinput(agent_id)

                    filtered_agent_state, agent_properties, action_class_name, action_kwargs = \
                        agent_obj.get_action_func(state=state, agent_properties=agent_obj.properties, agent_id=agent_id,
                                                  userinput=usrinp)
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

                # store the action in the buffer
                action_buffer[agent_id] = (action_class_name, action_kwargs)

                # Get all agents we have, as we need these to process all messages that are send to all agents
                all_agent_ids = self.__registered_agents.keys()

                # Obtain all communication messages if the agent has something to say to others (only comes here when
                # the agent is NOT busy)
                agent_messages = agent_obj.get_messages_func(all_agent_ids)
                if self.__run_matrxs_api:
                    if agent_id in api.messages:
                        # preprocess the messages received via the API, and add them to the agent's messages
                        agent_messages += AgentBrain.preprocess_messages(this_agent_id=agent_id,
                                                                         agent_ids=all_agent_ids,
                                                                         messages=api.messages[agent_id])
                        # clear the messages for the next tick
                        del api.messages[agent_id]
                if len(agent_messages) > 0:  # there are messages
                    # go through all messages
                    for mssg in agent_messages:
                        if mssg.to_id not in self.__message_buffer.keys():  # first message for this receiver
                            self.__message_buffer[mssg.to_id] = [mssg]
                        else:
                            self.__message_buffer[mssg.to_id].append(mssg)

            # save the current agent's state for the visualizer
            if self.__run_matrxs_api:
                api.add_state(agent_id=agent_id, state=filtered_agent_state, agent_inheritence_chain=agent_obj.class_inheritance)

        # save the god view state
        if self.__run_matrxs_api:
            api.add_state(agent_id="god", state=self.__get_complete_state(), agent_inheritence_chain="god")

            # make the information of this tick available via the API, after all
            # agents have been updated
            api.next_tick()
            api.current_tick = self.__current_nr_ticks
            # api.tick_duration = self.__tick_duration
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
            if receiver_id == None:
                # If receiver id is set to None, send to all registered agents
                for receiver_id in self.__registered_agents.keys():
                    self.__registered_agents[receiver_id].set_messages_func(messages)
            # check if the receiver exists
            elif receiver_id in self.__registered_agents.keys():
                # Call the callback method that sets the messages
                self.__registered_agents[receiver_id].set_messages_func(messages)
        # Clean the message buffer so we don't send the same messages next tick, but save it so it is accessible
        self.__messages_send_previous_tick = [mssg.content
                                              for mssg_list in self.__message_buffer.values()
                                              for mssg in mssg_list]
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
            print(
                f"@{os.path.basename(__file__)}: Tick {self.__current_nr_ticks} took {tick_duration.total_seconds()} seconds.")

        return self.__is_done, self.__curr_tick_duration

    def __check_simulation_goal(self):

        goal_status = {}
        if self.__simulation_goal is not None:
            if isinstance(self.__simulation_goal, list):
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
            self.add_to_grid(obj)
        for agent_id, agent in self.__registered_agents.items():
            self.add_to_grid(agent)

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
            "vis_settings": {
                "vis_bg_clr": self.__visualization_bg_clr,
                "vis_bg_img": self.__visualization_bg_img
            }
        }
        print("Timestamp now:", state['World']['curr_tick_timestamp'])

        return state

    def __get_agent_state(self, agent_obj: AgentBody):
        agent_loc = agent_obj.location
        sense_capabilities = agent_obj.sense_capability.get_capabilities()
        objs_in_range = OrderedDict()

        # Check which objects can be sensed with the agents' capabilities, from
        # its current position.
        for obj_type, sense_range in sense_capabilities.items():
            env_objs = self.get_objects_in_range(agent_loc, obj_type, sense_range)
            objs_in_range.update(env_objs)

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
            "vis_settings": {
                "vis_bg_clr": self.__visualization_bg_clr,
                "vis_bg_img": self.__visualization_bg_img
            }
        }
        print("Timestamp now:", state['World']['curr_tick_timestamp'])


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
            duration_in_ticks = 1

        else:  # action is not None

            # Get action class
            action_class = self.__all_actions[action_name]
            # Make instance of action
            action = action_class()

            # Obtain the duration of the action, defaults to the one of the action class if not in action_kwargs, and
            # otherwise that of Action
            duration_in_ticks = action.duration_in_ticks
            if "duration_in_ticks" in action_kwargs.keys():
                duration_in_ticks = action_kwargs["duration_in_ticks"]

        # The agent is now busy performing this action
        self.registered_agents[agent_id]._set_agent_busy(curr_tick=self.current_nr_ticks,
                                                         action_duration=duration_in_ticks)

        # Set the action and result in the agent so we know where the agent is busy with. In addition this is appended
        # to its properties so others know what agent did)
        self.registered_agents[agent_id]._set_current_action(action_name=action_name, action_args=action_kwargs)

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

    def __initial_visualisation(self):

        # Perform the initiali visualisation of the process is set and the boolean for running it is true
        if self.__run_visualization_server and self.__visualisation_process is None:
            # Loop through all agents, apply their observe to get their state for the gui
            for agent_id, agent_obj in self.__registered_agents.items():
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

    def __start_API(self):
        # bool to denote whether we succeeded in starting the API server
        succeeded = True

        # Set the server to debug mode if we are verbose
        # TODO Enable this when the debugging of the API is correct)
        # server.debug = self.__verbose

        # Create the process and run it
        api.run_api()
        self.__api_process = True


    def add_API_message_to_agent(self, message):
        print(message.content, message.from_id, message.to_id)

        if message.from_id in self.__registered_agents:
            agent = self.__registered_agents[message.from_id]

            msgs = agent.get_messages_func(None)

            print ("Agent messages:", msgs)


    @property
    def messages_send_previous_tick(self):
        return self.__messages_send_previous_tick

    @property
    def registered_agents(self):
        return self.__registered_agents

    @property
    def environment_objects(self):
        return self.__environment_objects

    @property
    def is_done(self):
        return self.__is_done

    @property
    def current_nr_ticks(self):
        return self.__current_nr_ticks

    @property
    def grid(self):
        return self.__grid

    @property
    def shape(self):
        return self.__shape

    @property
    def simulation_goal(self):
        return self.__simulation_goal

    @property
    def tick_duration(self):
        return self.__tick_duration
