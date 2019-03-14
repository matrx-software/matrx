import datetime
import math
import time
from collections import OrderedDict

import numpy as np

from environment.actions.move_actions import *
from environment.objects.basic_objects import AgentObject, EnvObject

ALL_ACTIONS = {  # Todo: Automatic discovery of this
    MoveNorth.__name__: MoveNorth,
    MoveNorthEast.__name__: MoveNorthEast,
    MoveEast.__name__: MoveEast,
    MoveSouthEast.__name__: MoveSouthEast,
    MoveSouth.__name__: MoveSouth,
    MoveSouthWest.__name__: MoveSouthWest,
    MoveWest.__name__: MoveWest,
    MoveNorthWest.__name__: MoveNorthWest,
}


class GridWorld:

    def __init__(self, shape, max_ticks, tick_duration, can_occupy_agent_locs=True, rnd_seed=1):
        self.tick_duration = tick_duration
        self.max_ticks = max_ticks
        self.registered_agents = OrderedDict()
        self.environment_objects = OrderedDict()
        self.current_ticks = 0
        # TODO : make goal assessment
        self.goal_assessment = None
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

    def register_agent(self, agent_name, location, sense_capability, action_set, get_action_func,
                       set_action_result_func, agent_properties, agent_type=AgentObject):
        agent_id = agent_name
        agent_seed = self.rnd_gen.randint(1)

        if not callable(get_action_func):
            raise Exception("The given agent 'get_action_func' is not callable. Please provide this method.")

        if agent_type == AgentObject:
            agent_object = AgentObject(agent_id=agent_id, agent_name=agent_name, location=location,
                                       sense_capability=sense_capability, action_set=action_set,
                                       get_action_func=get_action_func, properties=agent_properties,
                                       set_action_result_func=set_action_result_func)
        elif False:
            # TODO : You can add new agent that inherent from AgentObject that are more complex than the AgentObject.
            pass
        else:
            raise Exception(f"Agent of type {agent_type} is not known to the environment.")

        self.registered_agents[agent_id] = agent_object
        return agent_id, agent_seed

    def add_env_object(self, obj_name, location, obj_properties, is_passable=False):
        obj_id = obj_name
        env_object = EnvObject(obj_id, obj_name, locations=location, properties=obj_properties, is_passable=is_passable)

        self.environment_objects[obj_id] = env_object
        return obj_id

    def step(self):
        if self.current_ticks > self.max_ticks:
            self.is_done = True
            return self.is_done

        # current time of the tick start
        tick_start_time = datetime.datetime.now()

        # Go over all agents, detect what each can detect, figure out what actions are possible and send these to
        # that agent. Then receive the action back, store it in a buffer and go to the next agent. This blocks until
        # a response from the agent is received (hence a tick can take longer than self.tick_duration!!)
        action_buffer = OrderedDict()
        for agent_id, agent_obj in self.registered_agents.items():
            state = self.__get_agent_state(agent_obj)
            possible_actions = self.__get_possible_actions(agent_id=agent_id, action_set=agent_obj.action_set)
            action = agent_obj.get_action_func(state=state, possible_actions=possible_actions)
            action_buffer[agent_id] = action

        # Perform the actions in the order of the action_buffer (which is filled in order of registered agents
        for agent_id, action in action_buffer.items():
            self.__perform_action(agent_id, action)

        # Perform the update method of all objects
        for env_obj in self.environment_objects.values():
            # TODO work this out...
            env_obj.update_properties(self)

        # Update the grid
        self.__update_grid()

        # Check if we are done based on our global goal assessment function
        if self.goal_assessment is not None:
            self.is_done = self.goal_assessment.goal_reached(self)

        # Check if we reached max ticks
        if self.max_ticks <= self.current_ticks:
            self.is_done = True

        # Increment the number of tick we performed
        self.current_ticks += 1

        # Check how much time the tick lasted already
        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time
        self.curr_tick_duration = tick_duration.total_seconds()

        return self.is_done, tick_duration

    def sleep(self):
        """
        Sleeps the current python thread for the amount of time that is left after self.curr_tick_duration up to
        in self.tick_duration
        :return:
        """
        if self.tick_duration > 0:
            if self.curr_tick_duration < self.tick_duration:
                time.sleep(self.tick_duration - self.curr_tick_duration)
            else:
                pass
                # TODO : send warning/notification if the step takes longer

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

    def __get_agent_state(self, agent_obj):
        agent_loc = agent_obj.location
        sense_capabilities = agent_obj.sense_capability.get_capabilities()
        objs_in_range = []
        for obj_type, sense_range in sense_capabilities.items():
            env_objs = self.__get_objects_in_range(agent_loc, obj_type, sense_range)
            objs_in_range.extend(env_objs)

        state = {}
        for env_obj in objs_in_range:
            state[env_obj.name] = env_obj.properties

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

        # TODO Only return properties of object.

        return env_objs

    def __get_distance(self, coord1, coord2):
        dist = [(a - b) ** 2 for a, b in zip(coord1, coord2)]
        dist = math.sqrt(sum(dist))
        return dist

    def __get_possible_actions(self, action_set, agent_id):
        possible_actions = []
        for action_type in action_set:
            if action_type in ALL_ACTIONS:
                action_class = ALL_ACTIONS[action_type]
                action = action_class()
                is_possible = action.is_possible(grid_world=self, agent_id=agent_id)
                if is_possible:
                    possible_actions.append(action_type)
        # TODO return error when not possible
        return possible_actions

    def __perform_action(self, agent_id, action_name):
        if action_name is None:  # If action is not None
            result = ActionResult(ActionResult.NO_ACTION_GIVEN, succeeded=True)
        elif action_name in ALL_ACTIONS.keys():  # Check if action is known
            # Get action class
            action_class = ALL_ACTIONS[action_name]
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
