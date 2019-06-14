import warnings
from collections import OrderedDict

from environment.actions.move_actions import *


class WaypointNavigator:

    def __init__(self, agent_id):
        """
        This class represents a plan of high level actions. A high level action is for example exploring the top
        right corner while the agent is still located in the bottom left. This high level plan can then be translated
        to low level actions such as moving up or down.

        Parameters
        ----------
        agent_id : string
            The id of the agent that the plan belongs to. We need it so that we can look the agent up in the grid world.
        """
        self.__plan = []
        self.__current_idx = 0
        self.__agent_id = agent_id

    def add_waypoint(self, x, y, action=None, action_kwargs=None):
        """
        A method to add an item to the plan. On a location you want to perform a certain action.

        Parameters
        ----------
        x : integer
            The x coordinate of the planned action
        y : integer
            The y coordinate of the planned action
        action : Object
            The class name of an action to be taken. For example MoveEast.
        """
        plan_item = Waypoint(x, y, action, action_kwargs)
        self.__plan.append(plan_item)

    def next_basic_action(self, agent_state, possible_actions):
        """
        The agent wants to know what do next. It looks at the highest prio item in the plan, and performs a basic
        action that contributes to that step in the plan.

        Parameters
        ----------
        agent_state : dict The perceived environment in which we want to take the next action. It is needed so that we
        can derive a basic action from the plan
        possible_actions : [string] An array of strings of possible actions by the agent. Not all actions might always
        be possible.

        Returns
        ----------
        string
            A string representing the name of the class of the basic action to be taken. For example MoveEast.
        """
        if not self.is_finished():
            next_waypoint = self.__plan[self.__current_idx]
            action, action_kwargs = self.__plan_item_to_basic_action(next_waypoint, agent_state,
                                                                     possible_actions)
            return action, action_kwargs
        else:
            return None, {}

    def is_finished(self):
        """
        Returns whether all waypoints are followed or not.
        :return: True when all waypoints are navigated to, False if not.
        """
        return self.__current_idx >= len(self.__plan)

    def reset(self):
        """
        Resets the current waypoint navigator.
        """
        self.__plan = []
        self.__current_idx = 0

    def __plan_item_to_basic_action(self, waypoint, agent_state, possible_actions):
        """
        This function translates a plan item to a basic action. You are for example located in the bottom left corner
        of the grid world and your highest prio item is to extinguish a fire in the top right corner. The highest
        prio item is the extinguishing of the fire but you are located somewhere else. There fore you need to move
        first. This function makes this translation. The first implementation is rather rudimentary, as there are no
        objects that can block the road. If that is to happen, then this method should be extended with a planning
        component to find the best route.

        Parameters
        ----------
        waypoint : waypoint This is the item in the plan for which we want to compute a basic action
        agent_state : dict The environment in which we want to take the next action. It is needed so
        that we can derive a basic action from the plan
        possible_actions : [string] An array of strings of possible actions by the agent. Not all actions might always
        be possible.

        Returns
        ----------
        string
            A string representing the name of the class of the basic action to be taken. For example MoveEast.
        """
        location = agent_state[self.__agent_id]['location']

        # Perform navigation if the agent's location is different then the location of the plan item.
        if location[0] < waypoint.x and location[1] < waypoint.y and MoveSouthEast.__name__ in possible_actions:
            return MoveSouthEast.__name__, None

        elif location[0] < waypoint.x and location[1] > waypoint.y and MoveNorthEast.__name__ in possible_actions:
            return MoveNorthEast.__name__, None

        elif location[0] > waypoint.x and location[1] < waypoint.y and MoveSouthWest.__name__ in possible_actions:
            return MoveSouthWest.__name__, None

        elif location[0] > waypoint.x and location[1] > waypoint.y and MoveNorthWest.__name__ in possible_actions:
            return MoveNorthWest.__name__, None

        elif location[0] > waypoint.x and MoveWest.__name__ in possible_actions:
            return MoveWest.__name__, None

        elif location[0] < waypoint.x and MoveEast.__name__ in possible_actions:
            return MoveEast.__name__, None

        elif location[1] > waypoint.y and MoveNorth.__name__ in possible_actions:
            return MoveNorth.__name__, None

        elif location[1] < waypoint.y and MoveSouth.__name__ in possible_actions:
            return MoveSouth.__name__, None

        else:
            # If agent location is the same as the plan item's location, we check if the action is a possible action
            # when set and otherwise (when None) and return it. Otherwise we give a warning and return None and
            # action kwargs.
            if waypoint.action in possible_actions or waypoint.action is None:
                # At this point we actual perform
                self.__current_idx += 1
                return waypoint.action, waypoint.action_kwargs
            else:
                warnings.warn("")
                return None, {}

    def __str__(self):
        s = ""
        for idx, waypoint in enumerate(self.__plan):
            s = s + "[" + str(idx) + "] " + str(waypoint) + "\n"
        return s


class Waypoint:
    """
    This is a single plan item, which is a basic action on a specific location
    """

    def __init__(self, x=-1, y=-1, action=None, action_kwargs=None):
        self.x = x
        self.y = y
        self.action = action
        if action_kwargs is None:
            self.action_kwargs = {}
        else:
            self.action_kwargs = action_kwargs

    def __str__(self):
        return "(" + str(self.x) + "/" + str(self.y) + "-" + str(self.action) + ")"
