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
        """ Contains the decision logic of the agent.

        This method determines what action the human agent will perform. The GridWorld is responsible for deciding when
        an agent can perform an action again, if so this method is called for each agent. Two things need to be
        determined, which action and with what arguments.

        The action is returned simply as the class name (as a string), and the action arguments as a dictionary with the
        keys the names of the keyword arguments. An argument that is always possible is that of action_duration, which
        denotes how many ticks this action should take (e.g. a duration of 1, makes sure the agent has to wait 1 tick).

        Note; this function of the human_agent_brain overwrites the decide_on_action() function of the default agent,
        also providing the user input.


        Parameters
        ==========
        state : dict
            A state description containing all properties of EnvObject that are within a certain range as
            defined by self.sense_capability. It is a list of properties in a dictionary

        user_input: list
            A dictionary containing the key presses of the user, intended for controlling thus human agent.

        Returns
        =======
        action_name : str
            A string of the class name of an action that is also in self.action_set. To ensure backwards compatibility
            you could use Action.__name__ where Action is the intended action.

        action_args : dict
            A dictionary with keys any action arguments and as values the actual argument values. If a required argument
            is missing an exception is raised, if an argument that is not used by that action a warning is printed. The
            argument applicable to all action is `action_duration`, which sets the number ticks the agent is put on hold
            by the GridWorld until the action's world mutation is actual performed and the agent can perform a new
            action (a value of 0 is no wait, 1 means to wait 1 tick, etc.).
        """

        action_kwargs = {}


        action, kwargs = self.handle_context_move_to()
        if action is not None:
            return action, kwargs

        return action, action_kwargs

    def filter_observations(self, state):
        """
        All our agent work through the OODA-loop paradigm; first you observe, then you orient/pre-process, followed by
        a decision process of an action after which we act upon the action.

        However, as a human agent is controlled by a human, only the observe part is executed.

        This is the Observe phase. In this phase you filter the state further to only those properties the agent is
        actually SUPPOSED to see. Since the grid world returns ALL properties of ALL objects within a certain range(s),
        but perhaps some objects are obscured because they are behind walls, or an agent is not able to see some
        properties an certain objects.

        This filtering is what you do here.

        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :return: A filtered state.
        """
        return state

    def filter_user_input(self, user_input):
        """
        From the received userinput, only keep those which are actually Connected
        to a specific agent action
        """
        if user_input is None:
            return []
        possible_key_presses = list(self.key_action_map.keys())
        return list(set(possible_key_presses) & set(user_input))

    def __select_random_obj_in_range(self, state, range_, property_to_check=None):

        # Get all perceived objects
        object_ids = list(state.keys())

        # Remove world from state
        object_ids.remove("World")

        # Remove self
        object_ids.remove(self.agent_id)

        # Remove all (human)agents
        object_ids = [obj_id for obj_id in object_ids if "AgentBrain" not in state[obj_id]['class_inheritance'] and
                      "AgentBody" not in state[obj_id]['class_inheritance']]

        # find objects in range
        object_in_range = []
        for object_id in object_ids:

            # Select range as just enough to grab that object
            dist = int(np.ceil(np.linalg.norm(np.array(state[object_id]['location'])
                                              - np.array(state[self.agent_id]['location']))))
            if dist <= range_:
                # check for any properties specifically specified by the user
                if property_to_check is not None:
                    if property_to_check in state[object_id] and state[object_id][property_to_check]:
                        object_in_range.append(object_id)
                else:
                    object_in_range.append(object_id)

        # Select an object if there are any in range
        if object_in_range:
            object_id = self.rnd_gen.choice(object_in_range)
        else:
            object_id = None

        return object_id

    def fill_tasking_menu(self, selected_obj_id, target_obj_id):
        requester_agent_ID = self.agent_id
        context_menu = {
            "Move to...": self.context_move_to,
            "Say hi": self.context_pick_up
        }


    def context_say_hi(self, clicked_location, target_agent_id, target_object_id):
        # MATRX user method
        if target_agent_id is None or target_agent_id == self.agent_id:
            self.send_message(Message(content="Hi", from_id=self.agent_id))
        else:
            self.send_message(Message(content={"Hi": None}, from_id=self.agent_id, to_id=target_agent_id))

    def context_move_to(self, clicked_location, target_agent_id, target_obj_id):
        # MATRX user method
        if target_agent_id is None or target_agent_id == self.agent_id:
            self.move_to_loc = clicked_location
        else:
            self.send_message(content=Message({"move_to": clicked_location}), from_id=self.agent_id,
                              to_id=target_agent_id)


    # TODO: what is the use of this function?
    # def parse_context_messages():  # MATRX user method
    #     # Parse received message on a 'pick up' and/or 'move_to' messages, and set the brain's variables

    def handle_context_move_to(self):  # MATRX user method
        if self.move_to_loc is not None:
            # Apply the pathfinder to move to that location, set `move_to_loc` to None when done
            print("Moving to ", self.move_to_loc)

        return None, {}
