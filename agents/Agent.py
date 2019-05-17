import numpy as np

from environment.actions.object_actions import RemoveObject
from environment.actions.object_actions import GrabAction
from environment.actions.door_actions import *


class Agent:

    def __init__(self):
        """
        Creates an Agent. All other agents should inherit from this class if you want smarter agents. This agent
        simply randomly selects an action from the possible actions it can do.
        :param action_set: The actions the agent can perform. A list of strings, with each string a class name of an
        existing action in the package Actions.
        :param sense_capability: A SenseCapability object; it states which object types the agent can perceive within
        what range.
        :param agent_properties: the properties of this agent, including location etc.
        :param properties_agent_writable: which of the agent_properties can be changed by this agent
        :param grid_size: The size of the grid. The agent needs to send this along with other information to the
        webapp managing the Agent GUI
        """

        # Class variables for tracking the past action and its result
        self.previous_action = None
        self.previous_action_result = None

        # Filled by the WorldFactory during self.initialise
        self.agent_name = None
        self.action_set = None  # list of action names (strings)
        self.sense_capability = None
        self.rng = None
        self.rnd_seed = None
        self.agent_properties = {}
        self.keys_of_agent_writable_props = []

    def factory_initialise(self, agent_name, action_set, sense_capability, agent_properties, customizable_properties,
                           rnd_seed):
        """
        Called by the WorldFactory to initialise this agent with all required properties in addition with any custom
        properties. This also sets the random number generator with a seed generated based on the random seed of the
        world that is generated.

        Note; This method should NOT be overridden!

        :param agent_name: The name of the agent.
        :param action_set: The list of action names this agent is allowed to perform.
        :param sense_capability: The SenseCapability of the agent denoting what it can see withing what range.
        :param agent_properties: The dictionary of properties containing all mandatory and custom properties.
        :param customizable_properties: A list of keys in agent_properties that this agent is allowed to change.
        :param rnd_seed: The random seed used to set the random number generator self.rng
        """

        # The name of the agent with which it is also known in the world
        self.agent_name = agent_name

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

    def get_action(self, state, agent_properties, possible_actions, agent_id):
        """
        The function the environment calls. The environment receives this function object and calls it when it is time
        for this agent to select an action.
        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :param agent_properties: The properties of the agent, which might have been changed by the
        environment as a result of actions of this or other agents.
        :param possible_actions: The possible actions the agent can perform according to the grid world. The agent can
        send any other action (as long as it excists in the Action package), but these will not be performed in the
        world resulting in the appriopriate ActionResult.
        :param agent_id: the ID of this agent
        :return: The filtered state of this agent, the agent properties which the agent might have changed,
        and an action string, which is the class name of one of the actions in the Action package.
        """
        # Process any properties of this agent which were updated in the environment as a result of
        # actions
        self.agent_properties = agent_properties

        filtered_state = self.ooda_observe(state)
        state = self.ooda_orient(state)
        action, action_kwargs = self.ooda_decide(state, possible_actions)
        action = self.ooda_act(action)

        return filtered_state, self.agent_properties, action, action_kwargs

    def set_action_result(self, action_result):
        """
        A function that the environment calls (similarly as the self.get_action method) to set the action_result of the
        action this agent decided upon. Note, that the result is given AFTER the action is performed (if possible).
        Hence it is named the self.previous_action_result, as we can read its contents when we should decide on our
        NEXT action after the action whose result this is.
        :param action_result: An object that inherits from ActionResult, containing a boolean whether the action
        succeeded and a string denoting the reason why it failed (if it did so).
        :return:
        """
        self.previous_action_result = action_result

    def get_properties(self):
        """
        Returns all properties you want the grid world to have access to. These are the properties that other agents
        will receive when the observe this agent. Also, these are the properties that will be used to visualize the
        agent.

        By default we add the agent's name to the properties. The grid world is responsible for adding the location to
        it and any other default properties for the AgentAvatar class (the representation of the agent in the grid
        world).

        :return: A dictionary of properties, generally with strings as key and native types as values though is not
        required at all.
        """

        return self.agent_properties

    def set_rnd_seed(self, seed):
        """
        The function that seeds this agent's random seed.
        Currently; the grid world returns a seed for this agent and we need to set it 'manually' in our scenario script.
        In the future this will be done for us by the ScenarioManager.
        :param seed: The random seed this agent needs to be seeded with.
        :return:
        """
        self.rnd_seed = seed
        self.rnd_gen = np.random.RandomState(self.rnd_seed)

    def ooda_observe(self, state):
        """
        All our agent work through the OODA-loop paradigm; first you observe, then you orient/pre-process, followed by
        a decision process of an action after which we act upon the action.

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

    def ooda_orient(self, state):
        """
        All our agent work through the OODA-loop paradigm; first you observe, then you orient/pre-process, followed by
        a decision process of an action after which we act upon the action.

        This is the Orient phase. In this phase you can pre-process the state further. For example you can transform it
        in your desired state represantion, or add other knowledge to it you infer from all what is already in the
        state.

        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :return: A filtered state.
        """
        return state

    def ooda_decide(self, state, possible_actions):
        """
        All our agent work through the OODA-loop paradigm; first you observe, then you orient/pre-process, followed by
        a decision process of an action after which we act upon the action.

        This is the Decide phase. In this phase you actually compute your action. For example, this default agent simply
        randomly selects an action from the possible_actions list. However, for smarter agents you need the state
        representation for example to know what a good action is. In addition you should also return a dictionary of
        potential keyword arguments your intended action may require. You can set this to an empty dictionary if there
        are none. Though if you do not provide a required keyword argument (or wronly name it), the action will through
        an Exception and the environment will crash.

        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :param possible_actions: A list of strings of the action class names that are possible to do according to the
        grid world. This means that this list contain ALL actions this agent is allowed to do (as in; they are in
        self.action_set) and MAY result in a positive action result. This is not required (e.g.; a remove_object action
        might become impossible if another agent also decided to remove that object and who was a higher in the priority
        list).
        :return: An action string of the class name of an action that is also in self.action_set (it is not required to
        also be in possible_actions, though then the action will automatically fail.) You should also return a
        dictionary of action arguments the world might need to perform this action. See the implementation of the action
        to know which keyword arguments it requires. For example if you want to remove an object, you should provide
        it object ID with a specific key (e.g. 'object_id' = some_object_id_agent_should_remove).
        """
        if possible_actions:
            action = self.rnd_gen.choice(possible_actions)
        else:
            action = None

        action_kwargs = {}

        if action == RemoveObject.__name__:
            action_kwargs['object_id'] = None
        #     # Get all perceived objects
        #     objects = list(state.keys())
        #     # Remove yourself from the object id list
        #     objects.remove(self.agent_properties["obj_id"])
        #     # Remove all objects that have 'agent' in the name (so we do not remove those, though agents without agent
        #     # in their name can still be removed).
        #     objects = [obj for obj in objects if 'agent' not in obj]
        #     # Choose a random object id (safety for when it is empty)
        #     if objects:
        #         object_id = self.rnd_gen.choice(objects)
        #         # Assign it
        #         action_kwargs['object_id'] = object_id
        #         # Select range as just enough to remove that object
        #         remove_range = int(np.ceil(np.linalg.norm(
        #             np.array(state[object_id]['location']) - np.array(
        #                 state[self.agent_properties["obj_id"]]['location']))))
        #         # Safety for if object and agent are in the same location
        #         remove_range = max(remove_range, 0)
        #         # Assign it to the arguments list
        #         action_kwargs['remove_range'] = remove_range
        #     else:
        #         action_kwargs['object_id'] = None
        #         action_kwargs['remove_range'] = 0

        # if the agent randomly chose a grab action, choose a random object to pickup
        elif action == GrabAction.__name__:
            # Set grab range
            grab_range = 1

            # Set max amount of objects
            max_objects = 3

            # Assign it to the arguments list
            action_kwargs['grab_range'] = grab_range
            action_kwargs['max_objects'] = max_objects

            # Get all perceived objects
            objects = list(state.keys())

            # Remove yourself from the object id list
            objects.remove(self.agent_properties["obj_id"])
            # Remove all objects that have 'agent' in the name (so we do not remove those, though agents without agent
            # in their name can still be removed).
            objects = [obj for obj in objects if 'agent' not in obj]
            # Choose a random object id (safety for when it is empty)

            object_in_range = []
            for object_id in objects:
                # Select range as just enough to grab that object
                dist = int(np.ceil(np.linalg.norm(
                    np.array(state[object_id]['location']) - np.array(
                        state[self.agent_properties["obj_id"]]['location']))))
                if dist <= grab_range and state[object_id]["is_movable"]:
                    object_in_range.append(object_id)

            if object_in_range:
                # Select object
                object_id = self.rnd_gen.choice(object_in_range)

                # Assign it
                action_kwargs['object_id'] = object_id
            else:
                action_kwargs['object_id'] = None

        # if we randomly chose to do a open or close door action, find a door to open/close
        elif action == OpenDoorAction.__name__ or action == CloseDoorAction.__name__:

            action_kwargs['door_range'] = 1  # np.inf
            action_kwargs['object_id'] = None

            # Get all doors from the perceived objects
            objects = list(state.keys())
            doors = [obj for obj in objects if 'type' in state[obj] and state[obj]['type'] == "Door"]

            # choose a random door
            if len(doors) > 0:
                action_kwargs['object_id'] = self.rnd_gen.choice(doors)

        return action, action_kwargs

    def ooda_act(self, action):
        """
        All our agent work through the OODA-loop paradigm; first you observe, then you orient/pre-process, followed by
        a decision process of an action after which we act upon the action.

        This is the Act phase. In this phase you might perform a few things that the decided action also causes but is
        not done in and by the grid world itself. For example changing the battery level property of this agent.

        :param action: The decided action that may have additional consequences that are not performed by and in the
        grid world.
        :return: The decided action.
        """
        self.previous_action = action
        return action
