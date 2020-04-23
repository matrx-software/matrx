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

    def decide_on_action(self, state, user_input):

        for mssg in self.received_messages:
            print("Received a message! Contents:", mssg)

        action_kwargs = {}

        action = None
        action_kwargs = {}

        return action, action_kwargs


    def create_context_menu_for_self(self, clicked_object_id=None, click_location=None):
        """ For a context menu opened on specific object ID or click_location, return a lit of context menu options to
        display, with the resulting message that has to be sent.

        :param clicked_object_id:
        :param click_location:
        :return:
        """
        context_menu = []

        # create a menu item for every action
        for action in self.action_set:
            menu_item = self.add_action_context_item(menu_text=action, action_class_name=action, action_kwargs={})
            context_menu.append(menu_item)


        # append a custom menu item that sends a message
        menu_item = self.add_message_context_item(menu_text=f"Send object id {clicked_object_id} and loc "
                                                            f"{click_location} to self",
                                                  receiver=self.agent_id,
                                                  mssg_content={f"You, {self.agent_id}, opened a context menu on object"
                                                                f" {clicked_object_id} at loc {click_location}"})
        context_menu.append(menu_item)

        return context_menu



    def add_action_context_item(self, menu_text, action_class_name, action_kwargs):
        """ Add a context menu item that should trigger an Action being performed """
        return {
            "OptionText": menu_text,
            "OptionType": "action",
            "ActionName": action_class_name,
            "ActionKwargs": action_kwargs
        }


    def add_message_context_item(self, menu_text, receiver, mssg_content):
        """ Add a context menu item that sends a message with any contents """
        return {
            "OptionText": menu_text,
            "OptionType": "message",
            "MessageParameters": {"from": self.agent_id, "to": receiver, "content": mssg_content}
        }
