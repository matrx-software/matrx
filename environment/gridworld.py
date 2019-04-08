import datetime
import inspect
import math
import time
from collections import OrderedDict
import warnings

import numpy as np

from environment.actions.move_actions import *
from environment.objects.basic_objects import AgentAvatar, EnvObject

from visualization.helper_functions import sendGUIupdate


class GridWorld:

    def __init__(self, shape, tick_duration, simulation_goal=None, can_occupy_agent_locs=True, rnd_seed=1):
        self.tick_duration = tick_duration
        self.registered_agents = OrderedDict()
        self.environment_objects = OrderedDict()
        self.current_nr_ticks = 0
        self.simulation_goal = simulation_goal
        self.all_actions = self.__get_all_actions()
        self.current_available_id = 0
        self.can_occupy_agent_locs = can_occupy_agent_locs
        self.shape = shape
        self.grid = np.array([[None for x in range(shape[0])] for y in range(shape[1])])
        self.is_done = False
        self.rnd_seed = rnd_seed
        self.rnd_gen = np.random.RandomState(seed=self.rnd_seed)
        self.curr_tick_duration = 0.

    def initialize(self):
        # We update the grid, which fills everything with added objects and agents
        self.__update_grid()
        # We send all visible objects to the God view GUI
        self.__sync_god_view_GUI()

    def register_agent(self, agent_name, location, sense_capability, action_set, get_action_func,
                       set_action_result_func, agent_properties, agent_type=AgentAvatar):
        agent_id = agent_name
        agent_seed = self.rnd_gen.randint(1)

        if not callable(get_action_func):
            raise Exception("The given agent 'get_action_func' is not callable. Please provide this method.")

        if agent_type == AgentAvatar:
            agent_object = AgentAvatar(agent_id=agent_id, agent_name=agent_name, location=location,
                                       sense_capability=sense_capability, action_set=action_set,
                                       get_action_func=get_action_func, properties=agent_properties,
                                       set_action_result_func=set_action_result_func)
        else:
            raise Exception(f"Agent of type {agent_type} is not known to the environment.")

        # add colour and shape properties (for testing)
        agent_object.add_properties(propName="colour", propVal=np.random.choice(["#900C3F", "#581845"]))
        agent_object.add_properties(propName="shape", propVal=1)
        agent_object.add_properties(propName="size", propVal=1)
        agent_object.add_properties(propName="carrying", propVal = [])

        self.registered_agents[agent_id] = agent_object

        # XXX REMOVE TEMP XXX
        self.registered_agents[agent_id].once_carried = False

        return agent_id, agent_seed

    def add_env_object(self, obj_name, location, obj_properties, is_traversable=False):
        # This function adds the objects
        obj_id = obj_name
        env_object = EnvObject(obj_id, obj_name, locations=location, properties=obj_properties, is_traversable=is_traversable)
        env_object.add_properties(propName="carried", propVal=False)
        
        self.environment_objects[obj_id] = env_object
        return obj_id

    def step(self):

        # Check if we are done based on our global goal assessment function
        self.is_done = self.check_simulation_goal()

        # If this grid_world is done, we return immediately
        if self.is_done:
            return self.is_done, 0.

        # current time of the tick start
        tick_start_time = datetime.datetime.now()

        # Go over all agents, detect what each can detect, figure out what actions are possible and send these to
        # that agent. Then receive the action back, store it in a buffer and go to the next agent. This blocks until
        # a response from the agent is received (hence a tick can take longer than self.tick_duration!!)
        action_buffer = OrderedDict()
        for agent_id, agent_obj in self.registered_agents.items():
            state = self.__get_agent_state(agent_obj)
            possible_actions = self.__get_possible_actions(agent_id=agent_id, action_set=agent_obj.action_set)
            action = agent_obj.get_action_func(state=state, possible_actions=possible_actions, agent_id=agent_id)
            action_buffer[agent_id] = action

        # Perform the actions in the order of the action_buffer (which is filled in order of registered agents
        for agent_id, action in action_buffer.items():

            # XXX REMOVE TEMP XXX
            # Always perform a grab if possible
            if not self.registered_agents[agent_id].once_carried:
                result = self.__perform_action(agent_id, "GrabAction")
                if result.succeeded:
                    self.registered_agents[agent_id].once_carried = True

            self.__perform_action(agent_id, action)

        # Perform the update method of all objects
        for env_obj in self.environment_objects.values():
            env_obj.update_properties(self)

        # Update the grid
        self.__update_grid()
        self.__sync_god_view_GUI()

        # Increment the number of tick we performed
        self.current_nr_ticks += 1

        # Check how much time the tick lasted already
        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time
        self.curr_tick_duration = tick_duration.total_seconds()

        # Sleep for the remaining time of self.tick_duration
        self.__sleep()

        # Compute the total time of our tick (including potential sleep)
        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time
        self.curr_tick_duration = tick_duration.total_seconds()

        return self.is_done, self.curr_tick_duration

    def __sleep(self):
        """
        Sleeps the current python thread for the amount of time that is left after self.curr_tick_duration up to
        in self.tick_duration
        :return:
        """
        if self.tick_duration > 0:
            if self.curr_tick_duration < self.tick_duration:
                time.sleep(self.tick_duration - self.curr_tick_duration)
            else:
                self.__warn(f"The current tick took longer than the set tick duration of {self.tick_duration}")

    def check_simulation_goal(self):

        if self.simulation_goal is not None:
            if isinstance(self.simulation_goal, list):
                for sim_goal in self.simulation_goal:
                    is_done = sim_goal.goal_reached(self)
                    if is_done is False:
                        return False
            else:
                return self.simulation_goal.goal_reached(self)

        return False

    def __add_to_grid(self, grid_obj):
        if isinstance(grid_obj, EnvObject):
            if grid_obj.fills_multiple_locations:
                for loc in grid_obj.location:
                    if self.grid[loc[1], loc[0]] is not None:
                        self.grid[loc[1], loc[0]].append(grid_obj.obj_id)
                    else:
                        self.grid[loc[1], loc[0]] = [grid_obj.obj_id]
            else:
                loc = grid_obj.location
                if self.grid[loc[1], loc[0]] is not None:
                    self.grid[loc[1], loc[0]].append(grid_obj.obj_id)
                else:
                    self.grid[loc[1], loc[0]] = [grid_obj.obj_id]
        else:
            loc = grid_obj.location
            if self.grid[loc[1], loc[0]] is not None:
                self.grid[loc[1], loc[0]].append(grid_obj.obj_id)
            else:
                self.grid[loc[1], loc[0]] = [grid_obj.obj_id]

    def __update_grid(self):
        self.grid = np.array([[None for x in range(self.shape[0])] for y in range(self.shape[1])])
        for obj_id, obj in self.environment_objects.items():
            self.__add_to_grid(obj)
        for agent_id, agent in self.registered_agents.items():
            self.__add_to_grid(agent)


    # get all objects and agents on the grid
    def __get_complete_state(self):
        """
        Compile all objects and agents on the grid in one state dictionary
        :return: state with all objects and agents on the grid
        """

        # create a state with all objects and agents
        state = {}
        for obj_id, obj in self.environment_objects.items():
            state[obj.name] = obj.get_properties()
        for agent_id, agent in self.registered_agents.items():
            state[agent.name] = agent.get_properties()

        return state


    def __sync_god_view_GUI(self):
        # get all objects and agents on the grid
        state = self.__get_complete_state()

        # send the grid / god view state to the GUI web server for visualization
        sendGUIupdate(state=state, grid_size=self.shape, type="god", verbose=False)


    def __get_agent_state(self, agent_obj):
        agent_loc = agent_obj.location
        sense_capabilities = agent_obj.sense_capability.get_capabilities()
        objs_in_range = []

        # Check which objects can be sensed with the agents' capabilities, from
        # its current position.
        for obj_type, sense_range in sense_capabilities.items():
            env_objs = self.__get_objects_in_range(agent_loc, obj_type, sense_range)
            objs_in_range.extend(env_objs)

        state = {}
        # Save all properties of the sensed objects in a state dictionary
        for env_obj in objs_in_range:
            state[env_obj.name] = env_obj.get_properties()

        return state

    def __get_objects_in_range(self, agent_loc, object_type, sense_range):
        env_objs = []
        for _, env_obj in self.environment_objects.items():
            coordinates = env_obj.location
            distance = self.__get_distance(coordinates, agent_loc)
            if object_type is None or object_type == "*" or isinstance(env_obj, object_type) and \
                    distance <= sense_range:
                env_objs.append(env_obj)

        for _, agent_obj in self.registered_agents.items():
            coordinates = agent_obj.location
            distance = self.__get_distance(coordinates, agent_loc)

            if object_type is None or object_type == "*" or isinstance(agent_obj, object_type) and \
                    distance <= sense_range:
                env_objs.append(agent_obj)

        return env_objs

    def __get_distance(self, coord1, coord2):
        dist = [(a - b) ** 2 for a, b in zip(coord1, coord2)]
        dist = math.sqrt(sum(dist))
        return dist

    def __get_possible_actions(self, action_set, agent_id):
        possible_actions = []
        for action_type in action_set:
            if action_type in self.all_actions:
                action_class = self.all_actions[action_type]
                action = action_class()
                is_possible = action.is_possible(grid_world=self, agent_id=agent_id)
                if is_possible:
                    possible_actions.append(action_type)
        if len(possible_actions) == 0:
            warnings.warn(self.__warn("No possible actions for agent {agent_id}."))

        return possible_actions

    def __perform_action(self, agent_id, action_name):
        if action_name is None:  # If action is not None
            result = ActionResult(ActionResult.NO_ACTION_GIVEN, succeeded=True)
        elif action_name in self.all_actions.keys():  # Check if action is known
            # Get action class
            action_class = self.all_actions[action_name]
            # Make instance of action
            action = action_class()
            # Apply world mutation
            result = action.mutate(self, agent_id)
        else:  # If the action is not known
            result = ActionResult(ActionResult.UNKNOWN_ACTION, succeeded=False)
        # Get agent's send_result function
        set_action_result = self.registered_agents[agent_id].set_action_result_func
        # Send result of mutation to agent
        set_action_result(result)

        # Update world if needed
        if action_name is not None:
            self.__update_agent_location(agent_id)

        return result

    def __update_agent_location(self, agent_id):
        loc = self.registered_agents[agent_id].location
        if self.grid[loc[1], loc[0]] is not None:
            self.grid[loc[1], loc[0]].append(agent_id)
        else:
            self.grid[loc[1], loc[0]] = [agent_id]
    
    def __update_obj_location(self, obj_id): 
        loc = self.environment_objects[obj_id].location
        if self.grid[loc[1], loc[0]] is not None:
            self.grid[loc[1], loc[0]].append(obj_id)
        else:
            self.grid[loc[1], loc[0]] = [obj_id]        
    
    def __warn(self, warn_str):
        return f"[@{self.current_nr_ticks}] {warn_str}"

    def __get_all_actions(self):
        subclasses = set()
        work = [Action]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in subclasses:
                    subclasses.add(child)
                    work.append(child)

        act_dict = {}
        for action_class in subclasses:
            act_dict[action_class.__name__] = action_class

        return act_dict
