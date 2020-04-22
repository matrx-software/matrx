from matrx.actions.object_actions import GrabObject, DropObject, RemoveObject
from matrx.actions.door_actions import OpenDoorAction, CloseDoorAction
from matrx.agents import HumanAgentBrain
from matrx.agents.agent_utils.state_tracker import StateTracker
from matrx.agents.agent_brain import AgentBrain
import numpy as np

from matrx.messages import Message


class HumanAgentBrainContextTest(HumanAgentBrain):

    def __init__(self):
        super().__init__()
        self.move_to_loc = None


    def decide_on_action(self, state, user_input):


        action_kwargs = {}


        action, kwargs = self.handle_context_move_to()
        if action is not None:
            return action, kwargs

        return action, action_kwargs
