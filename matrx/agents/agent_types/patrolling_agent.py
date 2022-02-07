from matrx.agents import AgentBrain
from matrx.agents.agent_utils.navigator import Navigator
from matrx.agents.agent_utils.state_tracker import StateTracker


class PatrollingAgentBrain(AgentBrain):
    """ A simple agent that moves along a given path.

    """

    def __init__(self, waypoints, move_speed=0):
        """ Creates an agent brain to move along a set of waypoints.

        Parameters
        ----------
        waypoints : list
            The list of waypoints as (x,y) grid coordinates for the agent to move along.
        move_speed : int (Default: 0)
            This many ticks will be between each of the agent's move actions. When 0 or smaller, it will act on every
            tick. When 1 or higher, it will wait at least 1 or more ticks before moving again.
        """
        super().__init__()
        self.state_tracker = None
        self.navigator = None
        self.waypoints = waypoints
        self.move_speed = move_speed

    def initialize(self):
        """ Resets the agent's to be visited waypoints.

        This method is called each time a new world is created or the same world is reset. This prevents the agent to
        remember that it already moved and visited some waypoints.

        """
        # Initialize this agent's state tracker
        self.state_tracker = StateTracker(agent_id=self.agent_id)

        self.navigator = Navigator(agent_id=self.agent_id, action_set=self.action_set)

        self.navigator.add_waypoints(self.waypoints, is_circular=True)

    def filter_observations(self, state):
        """ Instead of filtering any observations, it just returns the given state.

        This means that the agent has no fancy observation mechanisms.

        Parameters
        ----------
        state : State
            The state object already filtered on the sensing range of the agent.

        Returns
        -------
        dict
            The unchanged State instance.

        """
        self.state_tracker.update(state)
        return state

    def decide_on_action(self, state):
        """ Makes use of the navigator to decide upon the next move action to get one step closer to the next waypoint.

        Parameters
        ----------
        state : State
            The State instance returned from `filter_observations`. In the case of this agent, that is the unchanged
            instance from the grid world who filtered only on the sensing range of this agent.

        Returns
        -------
        str
            The name of the next action.
        dict
            A dictionary containing any additional arguments for the action to perform. This agent provides the
            duration how long its move action should take.

        """
        from matrx.messages.message import Message

        move_action = self.navigator.get_move_action(self.state_tracker)

        return move_action, {"action_duration": self.move_speed}
