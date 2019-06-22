import numpy as np
import datetime
import requests

from agents.agent import Agent

from environment.actions.object_actions import GrabAction
from environment.actions.door_actions import *


class HumanAgent(Agent):

    def __init__(self):
        """
        Creates an Human Agent which is an agent that can be controlled by a human.
        """

        super().__init__()

    def factory_initialise(self, agent_name, agent_id, action_set, sense_capability, agent_properties,
                           customizable_properties, rnd_seed, usrinp_action_map={}):
        """
        Called by the WorldFactory to initialise this agent with all required properties in addition with any custom
        properties. This also sets the random number generator with a seed generated based on the random seed of the
        world that is generated.

        Note; This method should NOT be overridden!

        :param agent_name: The name of the agent.
        :param agent_id: The unique ID given by the world to this agent's avatar. So the agent knows what body is his.
        :param action_set: The list of action names this agent is allowed to perform.
        :param sense_capability: The SenseCapability of the agent denoting what it can see withing what range.
        :param agent_properties: The dictionary of properties containing all mandatory and custom properties.
        :param customizable_properties: A list of keys in agent_properties that this agent is allowed to change.
        :param rnd_seed: The random seed used to set the random number generator self.rng
        :param usrinp_action_map: maps userinputs (e.g. arrow key up) to a specific action
        """

        # The name of the agent with which it is also known in the world
        self.agent_name = agent_name

        # The id of the agent
        self.agent_id = agent_id

        # The names of the actions this agent is allowed to perform
        self.action_set = action_set

        # Setting the random seed and rng
        self.rnd_seed = rnd_seed
        self.set_rnd_seed(seed=rnd_seed)

        # The SenseCapability of the agent; what it can see and within what range
        self.sense_capability = sense_capability

        # Contains the agent_properties
        self.agent_properties = agent_properties

        # Specifies the keys of properties in self.agent_properties which can  be changed by this Agent in this file. If
        # it is not writable, it can only be  updated through performing an action which updates that property (done by
        # the environment).
        # NOTE: Changing which properties are writable cannot be done during runtime! Only in  the scenario manager
        self.keys_of_agent_writable_props = customizable_properties

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

        # only keep userinput which is actually connected to an agent action
        userinput = self.filter_userinputs(userinput)

        action_kwargs = {}

        # if there was no userinput do nothing
        if userinput is None or userinput == []:
            return state, self.agent_properties, None, {}

        # take the last userinput (for now), and fetch the action associated with that key
        userinput = userinput[-1]
        action = self.usrinp_action_map[userinput]

        # if the user chose a grab action, choose an object with a grab_range of 1
        if action == GrabAction.__name__:
            # Assign it to the arguments list
            action_kwargs['grab_range'] = 1  # Set grab range
            action_kwargs['max_objects'] = 3  # Set max amount of objects
            action_kwargs['object_id'] = None

            # Get all perceived objects
            objects = list(state.keys())

            # Remove all (human)agents
            objects = [obj for obj in objects if 'agent' not in obj.lower()]

            # find objects in range
            object_in_range = []
            for object_id in objects:
                if "is_movable" not in state[object_id]:
                    continue
                # Select range as just enough to grab that object
                dist = int(np.ceil(np.linalg.norm(
                    np.array(state[object_id]['location']) - np.array(
                        state[agent_id]['location']))))
                if dist <= action_kwargs['grab_range'] and state[object_id]["is_movable"]:
                    object_in_range.append(object_id)

            # Select an object if there are any in range
            if object_in_range:
                object_id = self.rnd_gen.choice(object_in_range)
                action_kwargs['object_id'] = object_id

        # if the user chose to do a open or close door action, find a door to open/close within 1 block
        elif action == OpenDoorAction.__name__ or action == CloseDoorAction.__name__:
            action_kwargs['door_range'] = 1
            action_kwargs['object_id'] = None

            # Get all doors from the perceived objects
            objects = list(state.keys())
            doors = [obj for obj in objects if 'door_open' in state[obj]]

            # get all doors within range
            doors_in_range = []
            for object_id in doors:
                # Select range as just enough to grab that object
                dist = int(np.ceil(np.linalg.norm(
                    np.array(state[object_id]['location']) - np.array(
                        state[self.agent_properties["name"]]['location']))))
                if dist <= action_kwargs['door_range']:
                    doors_in_range.append(object_id)

            # choose a random door within range
            if len(doors_in_range) > 0:
                action_kwargs['object_id'] = self.rnd_gen.choice(doors_in_range)

        # otherwise check which action is mapped to that key and return it
        return state, self.agent_properties, action, action_kwargs

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

    def filter_userinputs(self, userinputs):
        """
        From the received userinput, only keep those which are actually Connected
        to a specific agent action
        """
        if userinputs is None:
            return []
        possible_usrinpts = list(self.usrinp_action_map.keys())
        return list(set(possible_usrinpts) & set(userinputs))
