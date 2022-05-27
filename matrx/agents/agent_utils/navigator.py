import heapq
import warnings
from collections import OrderedDict

import numpy as np
from matrx.agents.agent_utils.state_tracker import StateTracker, get_traversability_map, get_weighted_traversability_map
from matrx.actions.move_actions import *


class Navigator:
    """ A navigator object that can be used for path planning and navigation.

    Parameters
    ----------
    agent_id: string
        ID of the agent that wants to navigate through a grid world.
    action_set: list
        List of actions the agent can perform.
    algorithm: string. Optional, default "a_star"
        The path planning algorithm to use. As of now only A* is supported.
    is_circular: bool (Default: False)
        When True, it will continuously navigate given waypoints, until infinity.

    Warnings
    --------
    This class still depends on the deprecated `StateTracker` instead of the new `State`. Note that the `StateTracker`
    is created from a state dictionary that can be obtained from a `State` instance. This is the current workaround to
    still make the `Navigator` work with the current `State`.

    Another approach is to not use `State` at all, and only rely on a `StateTracker`. See the
    :class:`matrx.agents.agent_types.patrolling_agent.PatrollingAgentBrain` which uses this approach.

    """

    """The A* algorithm parameter for path planning."""
    A_STAR_ALGORITHM = "a_star"
    WEIGHTED_A_STAR_ALGORITHM = "weighted_a_star"

    def __init__(self, agent_id, action_set, algorithm=A_STAR_ALGORITHM, custom_algorithm_class=None, traversability_map_func=get_traversability_map, 
                algorithm_settings={"metric": "euclidean"}, is_circular=False):
        # Set action set
        self.__action_set = action_set

        # Set the path planning algorithm, currently only A* is supported
        self.__algorithm = algorithm

        # Set the move action set the agent is capable of
        self.__move_actions = get_move_actions(action_set)

        # Set the agent ID
        self.__agent_id = agent_id

        # The function which calculates the traversability for a given state 
        self.__traversability_map_func = traversability_map_func
        
        # Initialize path plannings algorithm
        self.__path_planning_algo = self.__initialize_path_planner(algorithm=self.__algorithm, action_set=action_set, custom_algorithm_class=custom_algorithm_class, algorithm_settings=algorithm_settings)

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
        """ Adds a waypoint to the path.

        Parameters
        ----------
        waypoint: tuple, list
            The (x,y) coordinates of the cell.

        Raises
        ------
        AssertError
            When the waypoint is not a tuple or list.

        """

        assert isinstance(waypoint, tuple) or isinstance(waypoint, list)
        wp = Waypoint(loc=waypoint, priority=self.__nr_waypoints)
        self.__nr_waypoints += 1
        self.__waypoints[wp.priority] = wp

    def add_waypoints(self, waypoints, is_circular=False):
        """ Adds multiple waypoints to the path in order.

        Parameters
        ----------
        waypoints : list
            The list of waypoints of the form (x,y).
        is_circular : bool
            Whether the navigator should continuously visit all waypoints (including the ones already given before).

        Raises
        ------
        AssertError
            When the waypoint is not a tuple or list.

        """
        self.is_circular = is_circular

        for waypoint in waypoints:
            self.add_waypoint(waypoint)

    def get_all_waypoints(self, state_tracker: StateTracker=None):
        """ Returns all current waypoints stored.

        Returns
        -------
        dict
            A dictionary with as keys the order and as value the waypoint as (x,y) coordinate.

        """
        # Update our waypoints based on agent's current location (if arrived at our current waypoint)
        self.__update_waypoints(state_tracker)

        return [(k, wp.location) for k, wp in self.__waypoints.items()]

    def get_upcoming_waypoints(self, state_tracker: StateTracker=None):
        """ Returns all waypoints not yet visited.

        Returns
        -------
        dict
            A dictionary with as keys the order and as value the waypoint as (x,y) coordinate.

        """
        # Update our waypoints based on agent's current location (if arrived at our current waypoint)
        self.__update_waypoints(state_tracker)

        return [(k, wp.location) for k, wp in self.__waypoints.items() if not wp.is_visited()]

    def get_current_waypoint(self, state_tracker: StateTracker=None):
        """ Returns the current waypoint the navigator will try to visit.

        Returns
        -------
        list
            The (x,y) coordinate of the next waypoint.

        """
        # Update our waypoints based on agent's current location (if arrived at our current waypoint)
        self.__update_waypoints(state_tracker)
        
        wp = self.__waypoints[self.__current_waypoint_idx]
        return wp.location

    def get_move_action(self, state_tracker: StateTracker):
        """ Returns the next move action.

        It applies the path planning algorithm to identify the next best move action to move closer to the next
        waypoint.

        Parameters
        ----------
        state_tracker : StateTracker
            The state tracker used by the algorithm to determine what (according to what the agent observes) would be
            the best possible next move action.

        Returns
        -------
        str
            The name of the move action the agent is capable of making.

        Raises
        ------
        Warning
            Raises a warning (not exception) to signal that no path can be found to the next waypoint.

        ValueError
            Raised when the agent's location is not found on the route found by the path planning.

        """
        # If we are done, don't do anything
        if self.is_done and not self.is_circular:
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
        """ Resets all waypoints to not being visited.
        """
        self.is_done = False
        self.__current_waypoint_idx = 0
        for wp in self.__waypoints.values():
            wp.reset()

    def reset_full(self):
        """ Clears all waypoints to an empty Navigator.

        """
        # This function resets the navigator to a new instance
        self.__init__(self.__agent_id, self.__action_set, self.__algorithm, self.is_circular)

    def __get_current_waypoint(self):
        """ A private MATRX method.

        Returns
        -------
        Waypoint
            Returns the next waypoint object.

        """
        if self.__current_waypoint_idx is None:
            self.__current_waypoint_idx = 0

        if self.__current_waypoint_idx >= len(self.__waypoints):
            return None

        wp = self.__waypoints[self.__current_waypoint_idx]

        return wp

    def __initialize_path_planner(self, algorithm, action_set, custom_algorithm_class=None, algorithm_settings={}):
        """ A private MATRX method.

        Initializes the correct path planner algorithm.

        Parameters
        ----------
        algorithm : str
            The name of the algorithm to be used.
        action_set : list
            The list of actions the agent is capable of taking.

        Raises
        ------
        ValueError
            When the given algorithm is not known.

        """
        if algorithm == self.A_STAR_ALGORITHM:
            self.__traversability_map_func = get_traversability_map
            return AStarPlanner(action_set=action_set, settings=algorithm_settings)
        elif algorithm == self.WEIGHTED_A_STAR_ALGORITHM:
            self.__traversability_map_func = get_weighted_traversability_map
            return WeightedAStarPlanner(action_set=action_set, settings=algorithm_settings)
        elif algorithm != "" and custom_algorithm_class is not None:
            return custom_algorithm_class(action_set=action_set, settings=algorithm_settings)
        elif algorithm is None:
            raise ValueError(f"No path plannings algorithm was specified.")
        elif custom_algorithm_class is None:
            raise ValueError(f"A custom path planning algorithm called '{algorithm}' was specified, but no corresponding custom algorithm class was provided.")
        else:
            raise ValueError(f"Unknown path planning algorithm and/or path planning algorithm class was provided.")

    def __update_waypoints(self, state_tracker: StateTracker = None):
        """ A private MATRX method.

        Updates all is_visited property of waypoints based on the agent's current location. Also sets the navigator
        to done when all waypoints are visited.

        Parameters
        ----------
        agent_loc : list
            The agent's current location as (x,y)

        """
        if state_tracker is None:
            warnings.warn("Using the navigator without providing the `self.state_tracker` as a parameter to navigator functions is deprecated, as without it returns outdated waypoint information. Also see https://github.com/matrx-software/matrx/issues/316", DeprecationWarning)
            return False 
        else:
            # Get our agent's location
            agent_loc = state_tracker.get_memorized_state()[state_tracker.agent_id]['location']

        wp = self.__get_current_waypoint()
        if wp is not None and wp.is_visited(agent_loc):
            self.__current_waypoint_idx += 1

        if self.__current_waypoint_idx >= self.__nr_waypoints:
            self.is_done = True

    def __get_route(self, state_tracker: StateTracker):
        """ A private MATRX method.

        Applies the path planner algorithm based on the information in the given state tracker.

        Parameters
        ----------
        state_tracker : StateTracker
            The state tracker of the agent conducting the path planning. Used to represent all observations of the
            agent.

        Returns
        -------
        list
            A list of action strings the agent should conduct to arrive at the next waypoint. This route is empty when
            no path can be found or when all waypoints are already visited.

        """
        agent_loc = state_tracker.get_memorized_state()[state_tracker.agent_id]['location']

        # Update our waypoints based on agent's current location (if arrived at our current waypoint)
        self.__update_waypoints(state_tracker)

        # If we are done, we do nothing or start over if the path is circular
        if self.is_done:
            if self.is_circular:
                self.reset()
            else:
                return []

        # Get our occupation map
        self.__occupation_map, obj_grid = self.__traversability_map_func(state=state_tracker.get_memorized_state())

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
        """ A private MATRX method.

        Transforms a path of coordinates from the path planning algorithm to a series of actions.

        Parameters
        ----------
        agent_loc : tuple
            The agent's current location as (x,y).
        path : list
            List of coordinates that lead to the next waypoint.

        Returns
        -------
        list
            A list of strings of actions the agent is capable of taking to arrive at each path coordinate from the
            previous one (with the first being the agent's current location).

        """

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
    """ A private MATRX class.

    The empty path planner. Future path planning algorithms should implement this class.

    """

    def __init__(self, action_set, settings):
        """ Initializes the planner given the actions an agent is capable of.

        Parameters
        ----------
        action_set : list
            The list of actions the agent is capable of performing.
        settings : dict 
            A dict with settings for the pathplanner
        """
        self.move_actions = get_move_actions(action_set)
        self.settings = settings

    def plan(self, start, goal, occupation_map):
        """ Plan a route from the start to the goal.

        Parameters
        ----------
        start : tuple
            The starting (x,y) coordinate.
        goal : tuple
            The goal (x,y) coordinate.
        occupation_map : nparray
            The list of lists representing which grid coordinates are blocked and which are not.

        Returns
        -------
        list
            A list of coordinates the agent should visit in order to reach the goal coordinate.

        """
        pass


class AStarPlanner(PathPlanner):
    """ A* algorithm for path planning.
    """

    EUCLIDEAN_METRIC = "euclidean"
    MANHATTAN_METRIC = "manhattan"

    def __init__(self, action_set, settings):
        super().__init__(action_set, settings)

        metric = self.EUCLIDEAN_METRIC 
        if "metric" in settings:
            metric = settings['metric']
        
        if metric == self.EUCLIDEAN_METRIC:
            self.heuristic = lambda p1, p2: np.sqrt(np.sum((np.array(p1) - np.array(p2)) ** 2, axis=0))
        elif metric == self.MANHATTAN_METRIC:
            self.heuristic = lambda p1, p2: np.abs(p1[0] - p2[0]) + np.abs(p1[1] - p2[1])
        else:
            raise Exception(f"The distance metric {metric} for A* heuristic not known.")

    def plan(self, start, goal, occupation_map):
        """ Plan a route from the start to the goal.

        A* algorithm, returns the shortest path to get from goal to start.
        Uses an 2D numpy array, with 0 being traversable, anything else (e.g. 1) not traversable
        Implementation from:
        https://www.analytics-link.com/single-post/2018/09/14/Applying-the-A-Path-Finding-Algorithm-in-Python-Part-1-2D-square-grid

        Parameters
        ----------
        start : tuple
            The starting (x,y) coordinate.
        goal : tuple
            The goal (x,y) coordinate.
        occupation_map : list
            The list of lists representing which grid coordinates are blocked and which are not.

        Returns
        -------
        The list of coordinates to move to from start to finish.

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


class WeightedAStarPlanner(PathPlanner):
    """ Weighted A* algorithm for path planning.
    """

    EUCLIDEAN_METRIC = "euclidean"
    MANHATTAN_METRIC = "manhattan"

    def __init__(self, action_set, settings):
        super().__init__(action_set, settings)
            
        # parse settings 
        metric = self.EUCLIDEAN_METRIC if "metric" not in settings else settings['metric']
        self.traversability_penalty_multiplier = 10 if "traversability_penalty_multiplier" not in settings else settings['traversability_penalty_multiplier']

        if metric == self.EUCLIDEAN_METRIC:
            self.heuristic = lambda p1, p2: np.sqrt(np.sum((np.array(p1) - np.array(p2)) ** 2, axis=0))
        elif metric == self.MANHATTAN_METRIC:
            self.heuristic = lambda p1, p2: np.abs(p1[0] - p2[0]) + np.abs(p1[1] - p2[1])
        else:
            raise Exception(f"The distance metric {metric} for A* heuristic not known.")

    def plan(self, start, goal, occupation_map):
        """ Plan a route from the start to the goal.

        A* algorithm, returns the shortest path to get from goal to start.
        Uses an 2D numpy array, with 0 being traversable, anything else (e.g. 1) not traversable
        Implementation from:
        https://www.analytics-link.com/single-post/2018/09/14/Applying-the-A-Path-Finding-Algorithm-in-Python-Part-1-2D-square-grid

        Parameters
        ----------
        start : tuple
            The starting (x,y) coordinate.
        goal : tuple
            The goal (x,y) coordinate.
        occupation_map : list
            The list of lists representing which grid coordinates are blocked and which are not.

        Returns
        -------
        The list of coordinates to move to from start to finish.
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
                if 0 <= neighbor[0] < occupation_map.shape[0]:
                    if 0 <= neighbor[1] < occupation_map.shape[1]:
                        if occupation_map[neighbor[0]][neighbor[1]] == 1:
                            continue
                    else:
                        # array bound y walls
                        continue
                else:
                    # array bound x walls
                    continue
                

                # calc the cost of this route
                cost_multiplier = 1
                neighbor_traversability = occupation_map[neighbor[0]][neighbor[1]]
                # if the traversability is between 1 and 0, it indicates a preference. Higher scores should be avoided
                if neighbor_traversability < 1 and neighbor_traversability > 0:
                    cost_multiplier = self.traversability_penalty_multiplier * neighbor_traversability
                tentative_g_score = gscore[current] + (self.heuristic(current, neighbor) * cost_multiplier)

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
    """ A private MATRX class.

    Used to represent a navigation waypoint for the Navigator class.

    """

    def __init__(self, loc, priority):
        """ Creates a waypoint at a certain location with a priority.

        Parameters
        ----------
        loc : tuple
            The (x,y) coordinate of this waypoint.
        priority : int
            The priority in which this waypoint should be visited.
        """
        self.location = loc
        self.priority = priority
        self.__is_visited = False

    def is_visited(self, current_loc=None):
        """ Whether this waypoint is visited.

        Parameters
        ----------
        current_loc : list (Default: None)
            The (x,y) coordinate of an agent. When given, checks if this waypoint is visited by the agent on this
            location. Otherwise, performs no check.

        Returns
        -------
        bool
            Returns True when this waypoint is visited (or just now visited when `current_loc` is given). False
            otherwise.

        """
        if current_loc is None:
            return self.__is_visited
        elif current_loc[0] == self.location[0] and current_loc[1] == self.location[1] and not self.__is_visited:
            self.__is_visited = True

        return self.__is_visited

    def reset(self):
        """ Sets this waypoint as not visited.
        """
        self.__is_visited = False


def get_move_actions(action_set):
    """ Returns the names of all move actions in the given agent's action set.

    Parameters
    ----------
    action_set : list
        The names of all actions an agent can perform.

    Returns
    -------
    dict
        The dictionary of all move actions that are part of the agent's actions it can perform. The keys are the action
        names and values are the delta x and y effects on an agent's location.

    """
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
