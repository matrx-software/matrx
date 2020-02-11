from matrxs.agents.agent_brain import AgentBrain
from matrxs.utils.agent_utils.navigator import Navigator
from matrxs.utils.agent_utils.state_tracker import StateTracker


class PatrollingAgentBrain(AgentBrain):

    def __init__(self, waypoints, move_speed=1):
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
        from matrxs.utils.message import Message
        import random

        # Send a message to a random agent
        agents = []
        for obj_id, obj in state.items():

            if obj_id is "World":  # Skip the world properties
                continue

            classes = obj['class_inheritance']
            if AgentBrain.__name__ in classes:  # the object is an agent to which we can send our message
                agents.append(obj)
        selected_agent = self.rnd_gen.choice(agents)
        message_content = f"Hello, my name is {self.agent_name}"
        self.send_message(Message(content=message_content, from_id=self.agent_id, to_id=selected_agent['obj_id']))

        move_action = self.navigator.get_move_action(self.state_tracker)

        return move_action, {"action_duration": self.move_speed}