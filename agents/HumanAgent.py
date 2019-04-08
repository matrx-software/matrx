import numpy as np
import datetime
import requests

from visualization.helper_functions import sendGUIupdate

from agents.Agent import Agent


class HumanAgent(Agent):

    def __init__(self, name, action_set, sense_capability, usrinp_action_map, properties=None):
        """
        Creates an Human Agent which is an agent that can be controlled by a human.

        :param name: The name of the agent.
        :param strt_location: The initial location of the agent.
        :param action_set: The actions the agent can perform. A list of strings, with each string a class name of an
        existing action in the package Actions.
        :param sense_capability: A SenseCapability object; it states which object types the agent can perceive within
        what range.
        :param grid_size: The size of the grid. The agent needs to send this along with other information to the
        webapp managing the Agent GUI
        """

        super().__init__(name=name, action_set=action_set, sense_capability=sense_capability, properties=properties)

        self.usrinp_action_map = usrinp_action_map

    def get_action(self, state, possible_actions, agent_id):
        """
        The function the environment calls. The environment receives this function object and calls it when it is time
        for this agent to select an action.

        The function overwrites the default get_action() function for normal agents,
        and instead executes the action commanded by the user, which is received
        via the API of the visualization server.

        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :param possible_actions: The possible actions the agent can perform according to the grid world. The agent can
        send any other action (as long as it excists in the Action package), but these will not be performed in the
        world resulting in the appriopriate ActionResult.
        :return: An action string, which is the class name of one of the actions in the Action package.
        """
        # first filter the state to only show things this particular agent can see
        state = self.ooda_observe(state)

        # send the agent state to the GUI web server for visualization
        # sendGUIupdate(state=state, type="agent", verbose=True, id=agent_id)

        return state, None, {}


    # def get_action(self, state, possible_actions, agent_id):
    #     """
    #     The function the environment calls. The environment receives this function object and calls it when it is time
    #     for this agent to select an action.
    #
    #     The function overwrites the default get_action() function for normal agents,
    #     and instead executes the action commanded by the user, which is received
    #     via the API of the visualization server.
    #
    #     :param state: A state description containing all properties of EnvObject that are within a certain range as
    #     defined by self.sense_capability. It is a list of properties in a dictionary
    #     :param possible_actions: The possible actions the agent can perform according to the grid world. The agent can
    #     send any other action (as long as it excists in the Action package), but these will not be performed in the
    #     world resulting in the appriopriate ActionResult.
    #     :return: An action string, which is the class name of one of the actions in the Action package.
    #     """
    #
    #     # first filter the state to only show things this particular agent can see
    #     # state = self.ooda_observe(state)
    #
    #     # send the agent state to the GUI web server for visualization, and
    #     # receive the user input
    #     # userInput = sendGUIupdate(state=state, type="humanagent", verbose=False, id=agent_id)
    #     userInput = None
    #
    #     # if there was no userinput do nothing
    #     if userInput is None:
    #         return None, {}
    #
    #     print("human agent")
    #
    #     # otherwise check which action is mapped to that key and return it
    #     # return self.usrinp_action_map[userInput], {}
    #     return "lala", {"wut"}


    def ooda_observe(self, state):
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
