from matrx.agents import AgentBrain
from matrx.agents.agent_utils.navigator import Navigator
from matrx.agents.agent_utils.state_tracker import StateTracker


class PatrollingAgentBrain(AgentBrain):

    def __init__(self, waypoints, move_speed=0):
        super().__init__()
        self.state_tracker = None
        self.navigator = None
        self.waypoints = waypoints
        self.move_speed = move_speed

    def initialize(self):
        # Initialize this agent's state tracker
        self.state_tracker = StateTracker(agent_id=self.agent_id)

        self.navigator = Navigator(agent_id=self.agent_id, action_set=self.action_set,
                                   algorithm=Navigator.A_STAR_ALGORITHM)

        self.navigator.add_waypoints(self.waypoints, is_circular=True)

    def filter_observations(self, state):
        self.state_tracker.update(state)
        return state

    def decide_on_action(self, state):
        from matrx.messages.message import Message

        move_action = self.navigator.get_move_action(self.state_tracker)

        return move_action, {"action_duration": self.move_speed}