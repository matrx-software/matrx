from agents.utils.state_tracker import StateTracker
from environment.actions.door_actions import *
from environment.actions.object_actions import GrabAction
from environment.actions.object_actions import RemoveObject


class AgentBrain:

    def __init__(self):
        """
        Creates an Agent. All other agents should inherit from this class if you want smarter agents. This agent
        simply randomly selects an action from the possible actions it can do.
        """

        # Class variables for tracking the past action and its result
        self.previous_action = None
        self.previous_action_result = None

        # A list of messages that may be filled by this agent, which is retrieved by the GridWorld and send towards the
        # appropriate agents.
        self.messages_to_send = []
        self.received_messages = []

        # Filled by the WorldFactory during self.factory_initialise()
        self.agent_id = None
        self.agent_name = None
        self.action_set = None  # list of action names (strings)
        self.sense_capability = None
        self.rnd_gen = None
        self.rnd_seed = None
        self.agent_properties = {}
        self.keys_of_agent_writable_props = []

    def initialize(self):
        """
        Method called the very first time this AgentBrain is called from the world. Here you can initialize everything
        you need for your agent to work since you can't do much in the constructor as the brain needs to be connected to
        a GridWorld first in most cases (e.g. to get an AgentID, its random seed, etc.)
        """

    def filter_observations(self, state):
        """
        In this method you filter the state to only those properties and objects the agent is actually SUPPOSED to see.
        Since the grid world returns ALL properties of ALL objects within a certain range(s), but perhaps some objects
        are obscured because they are behind walls, or an agent is not able to see some properties an certain objects.

        This method is separated from the decide_on_action() method because it is also used by the GridWorld to make
        sure all UI's

        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :return: A filtered state.
        """

        return state

    def decide_on_action(self, state, possible_actions):
        """
        In this method you compute your action.

        For example, this default agent randomly selects an action from the possible_actions list. However,
        for smarter agents you need the state representation for example to know what a good action is. In addition
        you should also return a dictionary of potential keyword arguments your intended action may require. You can
        set this to an empty dictionary if there are none. Though if you do not provide a required keyword argument
        (or wrongly name it), the action will throw an Exception and the environment will crash.

        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :param possible_actions: A list of strings of the action class names that are possible to do according to the
        grid world. This means that this list contain ALL actions this agent is allowed to do (as in; they are in
        self.action_set) and MAY result in a positive action result. This is not required (e.g.; a remove_object action
        might become impossible if another agent also decided to remove that object and who was a higher in the priority
        list).
        :return: An action string of the class name of an action that is also in self.action_set. You should also return
        a dictionary of action arguments the world might need to perform this action. See the implementation of the
        action to know which keyword arguments it requires. For example if you want to remove an object, you should
        provide it object ID with a specific key (e.g. 'object_id' = some_object_id_agent_should_remove).
        """

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
        message = Message(content=message_content, from_id=self.agent_id, to_id=selected_agent['obj_id'])
        self.messages_to_send.append(message)

        # Select a random action
        if possible_actions:
            action = self.rnd_gen.choice(possible_actions)
        else:
            action = None

        action_kwargs = {}

        if action == RemoveObject.__name__:
            action_kwargs['object_id'] = None
            #
            # # Get all perceived objects
            # objects = list(state.keys())
            # # Remove yourself from the object id list
            # objects.remove(self.agent_properties["obj_id"])
            # # Remove all objects that have 'agent' in the name (so we do not remove those, though agents without agent
            # # in their name can still be removed).
            # objects = [obj for obj in objects if 'agent' not in obj]
            # # Choose a random object id (safety for when it is empty)
            # if objects:
            #     object_id = self.rnd_gen.choice(objects)
            #     # Assign it
            #     action_kwargs['object_id'] = object_id
            #     # Select range as just enough to remove that object
            #     remove_range = int(np.ceil(np.linalg.norm(
            #         np.array(state[object_id]['location']) - np.array(
            #             state[self.agent_properties["obj_id"]]['location']))))
            #     # Safety for if object and agent are in the same location
            #     remove_range = max(remove_range, 0)
            #     # Assign it to the arguments list
            #     action_kwargs['remove_range'] = remove_range
            # else:
            #     action_kwargs['object_id'] = None
            #     action_kwargs['remove_range'] = 0

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
            doors = [obj for obj in objects
                     if 'class_inheritance' in state[obj] and state[obj]['class_inheritance'][0] == "Door"]

            # choose a random door
            if len(doors) > 0:
                action_kwargs['object_id'] = self.rnd_gen.choice(doors)

        return action, action_kwargs

    def _factory_initialise(self, agent_name, agent_id, action_set, sense_capability, agent_properties,
                            customizable_properties, rnd_seed):
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
        """

        # The name of the agent with which it is also known in the world
        self.agent_name = agent_name

        # The id of the agent
        self.agent_id = agent_id

        # The names of the actions this agent is allowed to perform
        self.action_set = action_set

        # Setting the random seed and rng
        self.rnd_seed = rnd_seed
        self._set_rnd_seed(seed=rnd_seed)

        # The SenseCapability of the agent; what it can see and within what range
        self.sense_capability = sense_capability

        # Contains the agent_properties
        self.agent_properties = agent_properties

        # Specifies the keys of properties in self.agent_properties which can  be changed by this Agent in this file. If
        # it is not writable, it can only be  updated through performing an action which updates that property (done by
        # the environment).
        # NOTE: Changing which properties are writable cannot be done during runtime! Only in  the scenario manager
        self.keys_of_agent_writable_props = customizable_properties

    def _get_action(self, state, agent_properties, possible_actions, agent_id):
        """
        The function the environment calls. The environment receives this function object and calls it when it is time
        for this agent to select an action.

        Note; This method should NOT be overridden!

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
        # Process any properties of this agent which were updated in the environment as a result of actions
        self.agent_properties = agent_properties

        # Call the filter method to filter the observation
        filtered_state = self.filter_observations(state)

        # Call the method that decides on an action
        action, action_kwargs = self.decide_on_action(filtered_state, possible_actions)

        # Store the action so in the next call the agent still knows what it did
        self.previous_action = action

        # Return the filtered state, the (updated) properties, the intended actions and any keyword arguments for that
        # action if needed.
        return filtered_state, self.agent_properties, action, action_kwargs

    def _set_action_result(self, action_result):
        """
        A function that the environment calls (similarly as the self.get_action method) to set the action_result of the
        action this agent decided upon. Note, that the result is given AFTER the action is performed (if possible).
        Hence it is named the self.previous_action_result, as we can read its contents when we should decide on our
        NEXT action after the action whose result this is.

        Note; This method should NOT be overridden!

        :param action_result: An object that inherits from ActionResult, containing a boolean whether the action
        succeeded and a string denoting the reason why it failed (if it did so).
        :return:
        """
        self.previous_action_result = action_result

    def _set_rnd_seed(self, seed):
        """
        The function that seeds this agent's random seed.

        Note; This method should NOT be overridden!

        :param seed: The random seed this agent needs to be seeded with.
        :return:
        """
        self.rnd_seed = seed
        self.rnd_gen = np.random.RandomState(self.rnd_seed)

    def _get_messages(self):
        """
        This method is called by the GridWorld.

        Retrieves all message objects the agent has made in a tick, and returns those to the GridWorld for sending.
        It then removes all these messages!

        Note; This method should NOT be overridden!

        :return: A list of message objects with a generic content, the sender (this agent's id) and optionally a
        receiver. If a receiver is not set, the message content is send to all agents including this agent.
        """
        # Loop through all Message objects and create a dict out of each and append them to a list
        messages = []
        for mssg_obj in self.messages_to_send:
            messages.append(
                {'from_id': mssg_obj.from_id,
                 'to_id': mssg_obj.to_id,
                 'content': mssg_obj.content}
            )
        # Remove all messages that need to be send, as we have send them now
        self.messages_to_send = []

        return messages

    def _set_messages(self, messages):
        """
        This method is called by the GridWorld.
        It sets all messages intended for this agent to a list that it can access and read.

        Note; This method should NOT be overridden!

        :param messages: A list of dictionaries that contain a 'from_id', 'to_id' and 'content.
        """
        # We empty all received messages as this is from the previous tick
        self.received_messages = []
        # Loop through all messages and create a Message object out of the dictionaries.
        for mssg in messages:
            message_object = Message(from_id=mssg['from_id'], to_id=mssg['to_id'], content=mssg['content'])

            # Add the message object to the received messages
            self.received_messages.append(message_object)


class Message:
    """
    A simple object representing a communication message. An agent can create such a Message object by stating the
    content, its own id as the sender and (optinal) a receiver. If a receiver is not given it is a message to all
    agents, including the sender.
    """

    def __init__(self, content, from_id, to_id=None):
        self.content = content  # content can be anything; a string, a dictionary, or even a custom object
        self.from_id = from_id  # the agent id who creates this message
        self.to_id = to_id  # the agent id who is the sender, when None it means all agents, including the sende
