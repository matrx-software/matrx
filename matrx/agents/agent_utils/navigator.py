import heapq
import warnings
from collections import OrderedDict

import numpy as np
from matrx.agents.agent_utils.state_tracker import StateTracker
from matrx.actions.move_actions import *


class Navigator:
    """ A navigator object that can be used for path planning and navigation

    Parameters
    ----------
    agent_id: string.
        ID of the agent that wants to navigate
    action_set: list
        List of actions the agent can perform
    algorithm: string. Optional, default "a_star"
        The pathplanning algorithm to use. As of now only a_star is supported.
    is_circular: Boolean. Optional, default=False.
        Whether to continuously navigate from point A to B, and back, until infinity.
    """


    A_STAR_ALGORITHM = "a_star"

    def __init__(self, agent_id, action_set, algorithm=A_STAR_ALGORITHM, is_circular=False):
        # Set action set
        self.__action_set = action_set

        # Set the path planning algorithm, currently only A* is supported
        self.__algorithm = algorithm

        # Set the move action set the agent is capable of
        self.__move_actions = get_move_actions(action_set)

        # Set the agent ID
        self.__agent_id = agent_id

        # Initialize path plannings algorithm
        self.__path_planning_algo = self.__initialize_path_planner(algorithm=self.__algorithm, action_set=action_set)

        # An ordered dict to store all added waypoints
        self.__waypoints = OrderedDict()

        # Count the current number of waypoints we know of (used as key)
        self.__nr_waypoints = 0

        # Track which waypoint we are currently navigating to (if any)
        self.__current_waypoint_idx = None

        # An ordered dict to store the entire route through all waypoints
        self.__route = OrderedDict()

        # Boolean stating whether the navigator is done
        self.is_done = False

        # Boolean whether this navigator should navigate/patrol in a circular manner through all waypoints
        self.is_circular = is_circular

        # Current traversability map
        self.__occupation_map = None

    def add_waypoint(self, waypoint):
        assert isinstance(waypoint, tuple) or isinstance(waypoint, list)
        wp = Waypoint(loc=waypoint, priority=self.__nr_waypoints)
        self.__nr_waypoints += 1
        self.__waypoints[wp.priority] = wp

    def add_waypoints(self, waypoints, is_circular=False):
        self.is_circular = is_circular

        for waypoint in waypoints:
            self.add_waypoint(waypoint)

    def get_all_waypoints(self):
        return [(k, wp.location) for k, wp in self.__waypoints.items()]

    def get_upcoming_waypoints(self):
        return [(k, wp.location) for k, wp in self.__waypoints.items() if not wp.is_visited()]

    def get_current_waypoint(self):
        wp = self.__waypoints[self.__current_waypoint_idx]
        return wp.location

    def get_move_action(self, state_tracker: StateTracker):
        # If we are done, don't do anything
        if self.is_done:
            return None

        # Check if the state tracker is for the right agent
        assert state_tracker.agent_id == self.__agent_id

        route = self.__get_route(state_tracker)

        agent_loc = state_tracker.get_memorized_state()[self.__agent_id]['location']

        # if there is no route and we are done
        if len(route) == 0 and self.is_done:
            return None

        # if there is no route but we are not done, for example because a path
        # is blocked or we are already at the waypoint.
        elif len(route) == 0:  #
            agent_id = self.__agent_id
            current_wp = self.__get_current_waypoint()
            warnings.warn(f"The agent {agent_id} at {agent_loc} cannot find a "
                          f"path to the waypoint at {current_wp.location}, "
                          f"likely because it is blocked.", RuntimeWarning)
            return None

        # If the agent's location has a move action assigned to it
        elif agent_loc in route:
            move_action = route[agent_loc]

        # Otherwise we raise an exception that something went wrong
        else:
            agent_id = self.__agent_id
            raise ValueError(f"Something went wrong with the path planning. "
                            f"The location {agent_loc} of agent {agent_id} "
                            f"is not found in the route.")

        return move_action

    def reset(self):
        self.is_done = False
        self.__current_waypoint_idx = 0
        for wp in self.__waypoints.values():
            wp.reset()

    def reset_full(self):
        # This function resets the navigator to a new instance
        self.__init__(self.__agent_id, self.__action_set, self.__algorithm, self.is_circular)

    def __get_current_waypoint(self):
        if self.__current_waypoint_idx is None:
            self.__current_waypoint_idx = 0

        wp = self.__waypoints[self.__current_waypoint_idx]

        return wp

    def __initialize_path_planner(self, algorithm, action_set):
        if algorithm == self.A_STAR_ALGORITHM:
            return AStarPlanner(action_set=action_set, metric=AStarPlanner.EUCLIDEAN_METRIC)
        else:
            raise Exception()

    def __update_waypoints(self, agent_loc):
        wp = self.__get_current_waypoint()
        if wp.is_visited(agent_loc):
            self.__current_waypoint_idx += 1

        if self.__current_waypoint_idx >= self.__nr_waypoints:
            self.is_done = True

    def __get_route(self, state_tracker: StateTracker):
        # Get our agent's location
        agent_loc = state_tracker.get_memorized_state()[state_tracker.agent_id]['location']

        # Update our waypoints based on agent's current location (if arrived at our current waypoint)
        self.__update_waypoints(agent_loc)

        # If we are done, we do nothing or start over if the path is circular
        if self.is_done:
            if self.is_circular:
                self.reset()
            else:
                return []

        # Get our occupation map
        self.__occupation_map, obj_grid = state_tracker.get_traversability_map(inverted=True)

        # Get our current waypoint
        current_wp = self.__get_current_waypoint()

        # Plan a path using the chosen path planning algorithm
        path = self.__path_planning_algo.plan(start=agent_loc, goal=current_wp.location,
                                              occupation_map=self.__occupation_map)

        # Go over the path and select the action that is required to go from
        # one location to the other
        route = self.__get_route_from_path(agent_loc, path)

        return route

    def __get_route_from_path(self, agent_loc, path):
        route = {}
        curr_loc = agent_loc
        for idx, loc in enumerate(path):
            deltas = (loc[0] - curr_loc[0], loc[1] - curr_loc[1])
            if deltas not in self.__move_actions.values():
                agent_id = self.__agent_id
                raise Exception(f"Path leads from {curr_loc} to {loc} which requires a move of {deltas} which is not a "
                                f"possible move action for agent {agent_id}.")

            action = None
            for action_name, move_delta in self.__move_actions.items():
                if move_delta == deltas:
                    action = action_name

            route[curr_loc] = action

            curr_loc = loc

            if idx == len(path):
                route[loc] = None

        return route


class PathPlanner:

    def __init__(self, action_set):
        self.move_actions = get_move_actions(action_set)

    def plan(self, start, goal, occupation_map):
        pass


class AStarPlanner(PathPlanner):
    """ A* algorithm for path planning.
    """

    EUCLIDEAN_METRIC = "euclidean"
    MANHATTAN_METRIC = "manhattan"

    def __init__(self, action_set, metric=EUCLIDEAN_METRIC):
        super().__init__(action_set)
        if metric == self.EUCLIDEAN_METRIC:
            self.heuristic = lambda p1, p2: np.sqrt(np.sum((np.array(p1) - np.array(p2)) ** 2, axis=0))
        elif metric == self.MANHATTAN_METRIC:
            self.heuristic = lambda p1, p2: np.abs(p1[0] - p2[0]) + np.abs(p1[1] - p2[1])
        else:
            raise Exception(f"The distance metric {metric} for A* heuristic not known.")

    def plan(self, start, goal, occupation_map):
        """
        A star algorithm, returns the shortest path to get from goal to start.
        Uses an 2D numpy array, with 0 being traversable, anything else (e.g. 1) not traversable
        Implementation from:
        https://www.analytics-link.com/single-post/2018/09/14/Applying-the-A-Path-Finding-Algorithm-in-Python-Part-1-2D-square-grid
        """

        # possible movements
        neighbors = list(self.move_actions.values())

        close_set = set()
        came_from = {}
        gscore = {start: 0}
        fscore = {start: self.heuristic(start, goal)}
        oheap = []

        heapq.heappush(oheap, (fscore[start], start))

        while oheap:
            current = heapq.heappop(oheap)[1]

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]

            close_set.add(current)
            for i, j in neighbors:
                neighbor = current[0] + i, current[1] + j
                tentative_g_score = gscore[current] + self.heuristic(current, neighbor)
                if 0 <= neighbor[0] < occupation_map.shape[0]:
                    if 0 <= neighbor[1] < occupation_map.shape[1]:
                        if occupation_map[neighbor[0]][neighbor[1]] != 0:
                            continue
                    else:
                        # array bound y walls
                        continue
                else:
                    # array bound x walls
                    continue

                if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                    continue

                if tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1] for i in oheap]:
                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g_score
                    fscore[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(oheap, (fscore[neighbor], neighbor))

        # If no path is available we stay put
        return [start]


class Waypoint:

    def __init__(self, loc, priority):
        self.location = loc
        self.priority = priority
        self.__is_visited = False

    def is_visited(self, current_loc=None):
        if current_loc is None:
            return self.__is_visited
        elif current_loc[0] == self.location[0] and current_loc[1] == self.location[1] and not self.__is_visited:
            self.__is_visited = True

        return self.__is_visited

    def reset(self):
        self.__is_visited = False


def get_move_actions(action_set):
    move_actions = {}
    for action_name in action_set:
        if action_name == MoveNorth.__name__:
            move_actions[action_name] = (0, -1)
        elif action_name == MoveNorthEast.__name__:
            move_actions[action_name] = (1, -1)
        elif action_name == MoveEast.__name__:
            move_actions[action_name] = (1, 0)
        elif action_name == MoveSouthEast.__name__:
            move_actions[action_name] = (1, 1)
        elif action_name == MoveSouthWest.__name__:
            move_actions[action_name] = (-1, 1)
        elif action_name == MoveSouth.__name__:
            move_actions[action_name] = (0, 1)
        elif action_name == MoveWest.__name__:
            move_actions[action_name] = (-1, 0)
        elif action_name == MoveNorthWest.__name__:
            move_actions[action_name] = (-1, -1)

    # And moving nowhere is also possible
    move_actions[None] = (0, 0)

    return move_actions
