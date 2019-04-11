import numpy as np
import datetime
import requests

from agents.Agent import Agent


class HumanAgent(Agent):

    def __init__(self, action_set, sense_capability, usrinp_action_map, agent_properties,
                properties_agent_writable):
        """
        Creates an Human Agent which is an agent that can be controlled by a human.

        :param name: The name of the agent.
        :param strt_location: The initial location of the agent.
        :param action_set: The actions the agent can perform. A list of strings, with each string a class name of an
        existing action in the package Actions.
        :param sense_capability: A SenseCapability object; it states which object types the agent can perceive within
        what range.
        :param usrinp_action_map: maps userinputs (e.g. arrow key up) to a specific action
        :param agent_properties: the properties of this agent, including location etc.
        :param properties_agent_writable: which of the agent_properties can be changed by this agent
        """

        super().__init__(   action_set=action_set,
                            sense_capability=sense_capability,
                            agent_properties=agent_properties,
                            properties_agent_writable=properties_agent_writable)

        # specifies the agent_properties
        self.agent_properties = agent_properties
        # specifies the keys of properties in self.agent_properties which can
        # be changed by this Agent in this file. If it is not writable, it can only be
        # updated through performing an action which updates that property (done by the environment).
        # NOTE: Changing which properties are writable cannot be done during runtime! Only in
        # the scenario manager
        self.keys_of_agent_writable_props = properties_agent_writable

        # a list which maps user inputs to actions, defined in the scenario manager
        self.usrinp_action_map = usrinp_action_map


    def get_action(self, state, agent_properties, possible_actions, agent_id, userinput):
        """
        The function the environment calls. The environment receives this function object and calls it when it is time
        for this agent to select an action.

        The function overwrites the default get_action() function for normal agents,
        and instead executes the action commanded by the user, which is received
        via the API of the visualization server.

        :param state: A state description containing all properties of EnvObject that are detectable by this agent,
        i.e. within the detectable range as defined by self.sense_capability. It is a list of properties in a dictionary
        :param agent_properties: The properties of the agent, which might have been changed by the
        environment as a result of actions of this or other agents.
        :param possible_actions: The possible actions the agent can perform according to the grid world. The agent can
        send any other action (as long as it excists in the Action package), but these will not be performed in the
        world resulting in the appriopriate ActionResult.
        :param agent_id: the ID of this agent
        :param userinput: any userinput given by the user for this human agent via the GUI
        :return: The filtered state of this agent, the agent properties which the agent might have changed,
        and an action string, which is the class name of one of the actions in the Action package.
        """
        # Process any properties of this agent which were updated in the environment as a result of
        # actions
        self.agent_properties = agent_properties

        # first filter the state to only show things this particular agent can see
        state = self.ooda_observe(state)

        # if there was no userinput do nothing
        if userinput is None:
            return state, self.agent_properties, None, {}

        # otherwise check which action is mapped to that key and return it
        return state, self.agent_properties, self.usrinp_action_map[userinput], {}




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
