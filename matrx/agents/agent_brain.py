import copy
import json
import warnings

import numpy as np
from matrx.actions import GrabObject, RemoveObject, OpenDoorAction, CloseDoorAction
from matrx.agents.agent_utils.state import State
from matrx.messages import Message


class AgentBrain:
    """ An artificial agent whose behaviour can be programmed to be, for example, (semi-)autonomous.
    """

    def __init__(self, memorize_for_ticks=None):
        """ Defines the behavior of an agent.

        This class is the place where all the decision logic of an agent is
        contained. This class together with the
        :class:`matrx.objects.agent_body.AgentBody` class represent a full agent.

        This agent brain simply selects a random action from the possible actions
        it can do.

        When you wish to create a new agent, this is the class you need
        to extend. In specific these are the functions you should override:

        * :meth:`matrx.agents.agent_brain.initialize`
            Called before a world starts running. Can be used to initialize
            variables that can only be initialized after the brain is connected to
            its body (which is done by the world).
        * :meth:`matrx.agents.agent_brain.filter_observations`
            Called before deciding on an action to allow detailed and agent
            specific filtering of the received world state.
        * :meth:`matrx.agents.agent_brain.decide_on_action`
            Called to decide on an action.
        * :meth:`matrx.agents.agent_brain.get_log_data`
            Called by data loggers to obtain data that should be logged from this
            agent internal reasoning.

        Attributes
        ----------
        action_set: [str, ...]
            List of actions this agent can perform.
        agent_id: str
            The unique identified of this agent's body in the world.
        agent_name: str
            The name of this agent.
        agent_properties: dict
            A dictionary of this agent's
            :class:`matrx.objects.agent_body.AgentBody` properties. With as keys
            the property name, and as value the property's value.

            These can be adjusted iff they are said to be adjustable (e.g. inside
            the attribute `keys_of_agent_writable_props`).
        keys_of_agent_writable_props: [str, ...]
            List of property names that this agent can adjust.
        messages_to_send: [Message, ...]
            List of messages this agent will send. Use the method
            :meth:`matrx.agents.agent_brain.AgentBrain.send_message` to append to
            this list.
        previous_action: str
            The name of the previous performed or attempted action.
        previous_action_result: ActionResult
            The :class:`matrx.actions.action.ActionResult` of the previously
            performed or attempted action.
        received_messages: [Message, ...]
            The list of received messages.
        rnd_gen: Random
            The random generator for this agent.
        rnd_seed: int
            The random seed with which this agent's `rnd_gen` was initialized. This
            seed is based on the master random seed given of the
            :class:`matrx.grid_world.GridWorld`.
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
        self.__memorize_for_ticks = memorize_for_ticks

        # The central state property (an extended dict with unique searching capabilities)
        self._state = None

    def initialize(self):
        """ To initialize an agent's brain.

        Method called at the start of a :class:`matrx.grid_world.GridWorld`.

        Here you can initialize everything you need for your agent to work
        since you can't do much in the constructor as the brain needs to be
        connected to a GridWorld first in most cases (e.g. to get an AgentID,
        its random generator, etc.)
        """

    def filter_observations(self, state):
        """ Filters the world state before deciding on an action.

        In this method you filter the received world state to only those
        properties and objects the agent is actually supposed to see.

        Currently the world returns ALL properties of ALL objects within a
        certain range(s), as specified by :
        class:`matrx.agents.capabilities.capability.SenseCapability`. But
        perhaps some objects are obscured because they are behind walls and
        this agent is not supposed to look through walls, or an agent is not
        able to see some properties of certain objects (e.g. colour).

        The adjusted world state that this function returns is directly fed to
        the agent's decide function. Furthermore, this returned world state is
        also fed through the MATRX API to any visualisations.

        Override this method when creating a new AgentBrain and you need to
        filter the world state further.

        Parameters
        ----------
        state: State
            A state description containing all perceived
            :class:`matrx.objects.env_object.EnvObject` and objects inheriting
            from this class within a certain range as defined by the
            :class:`matrx.agents.capabilities.capability.SenseCapability`.

            The keys are the unique identifiers, as values the properties of
            an object. See :class:`matrx.objects.env_object.EnvObject` for the
            kind of properties that are always included. It will also contain
            all properties for more specific objects that inherit from that
            class.

            Also includes a 'world' key that describes common information about
            the world (e.g. its size).

        Returns
        -------
        filtered_state : State
            A dictionary similar to `state` but describing the filtered state
            this agent perceives of the world.

        Notes
        -----
        A future version of MATRX will include handy utility function to make
        state filtering less of a hassle (e.g. to easily remove specific
        objects or properties, but also ray casting to remove objects behind
        other objects)

        """

        return state

    def decide_on_action(self, state):
        """ Contains the decision logic of the agent.

        This method determines what action the agent should perform. The
        :class:`matrx.grid_world.GridWorld` is responsible for deciding when
        an agent can perform an action, if so this method is called for each
        agent and fed with the world state from the `filter_observations`
        method.

        Two things need to be determined: action name and action arguments.

        The action is returned simply as the class name (as a string), and the
        action arguments as a dictionary with the keys the names of the keyword
        arguments. See the documentation of that action to find out which
        arguments.

        An argument that is always possible is that of action_duration, which
        denotes how many ticks this action should take and overrides the
        action duration set by the action implementation.

        Parameters
        ----------
        state : State
        A state description as given by the agent's
        :meth:`matrx.agents.agent_brain.AgentBrain.filter_observation` method.

        Returns
        -------
        action_name : str
            A string of the class name of an action that is also in the
            `action_set` class attribute. To ensure backwards compatibility
            we advise to use Action.__name__ where Action is the intended
            action.

        action_args : dict
            A dictionary with keys any action arguments and as values the
            actual argument values. If a required argument is missing an
            exception is raised, if an argument that is not used by that
            action a warning is printed. The argument applicable to all action
            is `action_duration`, which sets the number ticks the agent is put
            on hold by the GridWorld until the action's world mutation is
            actual performed and the agent can perform a new action (a value of
            0 is no wait, 1 means to wait 1 tick, etc.).

        Notes
        -----
        A future version of MATRX will include handy utility function to make
        agent decision-making less of a hassle. Think of a
        Belief-Desire-Intention (BDI) like structure, and perhaps even support
        for learning agents.
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
        self.send_message(Message(content=message_content, from_id=self.agent_id, to_id=selected_agent['obj_id']))

        # Select a random action
        if self.action_set:
            action = self.rnd_gen.choice(self.action_set)
        else:
            action = None

        action_kwargs = {}

        if action == RemoveObject.__name__:
            action_kwargs['object_id'] = None

            # Get all perceived objects
            objects = list(state.keys())
            # Remove yourself from the object id list
            objects.remove(self.agent_properties["obj_id"])
            # Remove all objects that have 'agent' in the name (so we do not remove those, though agents without agent
            # in their name can still be removed).
            objects = [obj for obj in objects if 'agent' not in obj]
            # Choose a random object id (safety for when it is empty)
            if objects:
                object_id = self.rnd_gen.choice(objects)
                # Assign it
                action_kwargs['object_id'] = object_id
                # Select range as just enough to remove that object
                remove_range = int(np.ceil(np.linalg.norm(
                    np.array(state[object_id]['location']) - np.array(
                        state[self.agent_properties["obj_id"]]['location']))))
                # Safety for if object and agent are in the same location
                remove_range = max(remove_range, 0)
                # Assign it to the arguments list
                action_kwargs['remove_range'] = remove_range
            else:
                action_kwargs['object_id'] = None
                action_kwargs['remove_range'] = 0

        # if the agent randomly chose a grab action, choose a random object to pickup
        elif action == GrabObject.__name__:
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

    def get_log_data(self):
        """ Provides a dictionary of data for any Logger

        This method functions to relay data from an agent's decision logic (this AgentBrain class) through the GridWorld
        into a Logger. Here it can be further processed and stored.

        Returns
        -------
        data : dict
            A dictionary with keys identifiable names and the data as its value.
        """
        return {}

    def send_message(self, message):
        """  Sends a Message from this agent to others

        Method that allows you to construct a message that will be send to either a specified agent, a team of agents
        or all agents.

        Parameters
        ----------
        message: Message
            A message object that needs to be send. Should be of type Message. It's to_id can contain a single
            recipient, a list of recipients or None. If None, it is send to all other agents.

        """
        # Check if the message is a true message
        self.__check_message(message, self.agent_id)
        # Add the message to our list
        self.messages_to_send.append(message)

    def is_action_possible(self, action, action_kwargs):
        """ Checks if an action would be possible.

        This method can be called from the AgentBrain to check if a certain action is possible to perform with the
        current state of the GridWorld. It requires as input an action name and its arguments (if any), same as the
        decide_on_action method should return.

        This method does not guarantees that if the action is return by the brain it actually succeeds, as other agents
        may intervene.

        Parameters
        ----------
        action : str
            The name of an Action class.
        action_kwargs : dict
            A dictionary with keys any action arguments and as values the actual argument values.

        Returns
        -------
        succeeded : bool
            True if the action can be performed, False otherwise.
        action_results : ActionResult
            An ActionResult object containing the success or failure of the action, and (if failed) the reason why.

        """
        action_result = self.__callback_is_action_possible(self.agent_id, action, action_kwargs)

        return action_result.succeeded, action_result

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):

        # Check if the return filtered state is a differently created State
        # object, if so, raise the warning that we are overwriting it.
        if new_state is not self.state:
            warnings.warn(f"Overwriting State object of {self.agent_id}. This "
                          f"will cause any stored memory to be gone for good "
                          f"as this was stored in the previous State object.")

        if isinstance(new_state, dict):
            raise TypeError(f"The new state should of type State, is of "
                            f"type {new_state.__class__}")

        self._state = new_state

    @property
    def memorize_for_ticks(self):
        return self.__memorize_for_ticks

    def create_context_menu_for_other(self, agent_id_who_clicked, clicked_object_id, click_location):
        """ Generate options for a context menu for a specific object/location that a user NOT controlling this
        human agent opened.

        Thus: another human agent selected this agent, opened a context menu by right clicking on an object or location.
        This function is called. It should return actions, messages, or other info for what this agent can do relevant
        to that object / location. E.g. pick it up, move to it, display information on it, etc.

        Example usecase: tasking another agent that is not yourself, e.g. to move to a specific location.

        For the default MATRX visualization, the context menu is opened by right clicking on an object. This function
        should generate a list of options (actions, messages, or something else) which relate to that object or location.
        Each option is in the shape of a text shown in the context menu, and a message which is send to this agent if
        the user actually clicks that context menu option.

        Parameters
        ----------
        agent_id_who_clicked : str
            The ID of the (human) agent that selected this agent and requested for a context menu.
        clicked_object_id : str
            A string indicating the ID of an object. Is None if the user clicked on a background tile (which has no ID).
        click_location : list
            A list containing the [x,y] coordinates of the object on which the user right clicked.

        Returns
        -------
         context_menu : list
            A list containing context menu items. Each context menu item is a dict with a 'OptionText' key, which is
            the text shown in the menu for the option, and a 'Message' key, which is the message instance that is sent
            to this agent when the user clicks on the context menu option.
        """
        print("Context menu other")
        context_menu = []

        # Generate a context menu option for every action
        for action in self.action_set:
            context_menu.append({
                "OptionText": f"Do action: {action}",
                "Message": Message(content=action, from_id=clicked_object_id, to_id=self.agent_id)
            })
        return context_menu

    def _factory_initialise(self, agent_name, agent_id, action_set, sense_capability, agent_properties,
                            customizable_properties, rnd_seed, callback_is_action_possible):
        """ Private MATRX function.

        Initialization of the brain by the WorldBuilder.

        Called by the WorldFactory to initialise this agent with all required properties in addition with any custom
        properties. This also sets the random number generator with a seed generated based on the random seed of the
        world that is generated.

        Parameters
        ----------
        agent_name : str
            The name of the agent.
        agent_id : str
            The unique ID given by the world to this agent's avatar. So the agent knows what body is his.
        action_set : str
            The list of action names this agent is allowed to perform.
        sense_capability : SenseCapability
            The SenseCapability of the agent denoting what it can see withing what range.
        agent_properties : dict
            The dictionary of properties containing all mandatory and custom properties.
        customizable_properties : list
            A list of keys in agent_properties that this agent is allowed to change.
        rnd_seed : int
            The random seed used to set the random number generator self.rng
        callback_is_action_possible : callable
            A callback to a GridWorld method that can check if an action is possible.

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

        # Initializing the State object
        self._init_state()

        # The SenseCapability of the agent; what it can see and within what range
        self.sense_capability = sense_capability

        # Contains the agent_properties
        self.agent_properties = agent_properties

        # Specifies the keys of properties in self.agent_properties which can  be changed by this Agent in this file. If
        # it is not writable, it can only be  updated through performing an action which updates that property (done by
        # the environment).
        # NOTE: Changing which properties are writable cannot be done during runtime! Only when adding it to the world.
        self.keys_of_agent_writable_props = customizable_properties

        # A callback to the GridWorld instance that can check whether any action (with its arguments) will succeed and
        # if not why not (in the form of an ActionResult).
        self.__callback_is_action_possible = callback_is_action_possible

    def _get_action(self, state, agent_properties, agent_id):
        """ Private MATRX function

        The function the environment calls. The environment receives this function object and calls it when it is time
        for this agent to select an action.

        Note; This method should NOT be overridden!

        Parameters
        ----------
        state_dict: dict
            A state description containing all properties of EnvObject that are within a certain range as defined by
            self.sense_capability. It is a list of properties in a dictionary
        agent_properties: dict
            The properties of the agent, which might have been changed by the environment as a result of actions of
            this or other agents.
        agent_id: str
            the ID of this agent

        Returns
        -------
         filtered_state : dict
            The filtered state of this agent
        agent_properties : dict
            the agent properties which the agent might have changed,
        action : str
            an action string, which is the class name of one of the actions in the Action package.
        action_kwargs : dict
            Keyword arguments for the action

        """
        # Process any properties of this agent which were updated in the environment as a result of actions
        self.agent_properties = agent_properties

        # Update the state property of an agent with the GridWorld's state dictionary
        self.state.state_update(state)

        # Call the filter method to filter the observation
        self.state = self.filter_observations(self.state)

        # Call the method that decides on an action
        action, action_kwargs = self.decide_on_action(self.state)

        # Store the action so in the next call the agent still knows what it did
        self.previous_action = action

        # Get the dictionary from the State object
        filtered_state = self.state.as_dict()

        # Return the filtered state, the (updated) properties, the intended actions and any keyword arguments for that
        # action if needed.
        return filtered_state, self.agent_properties, action, action_kwargs

    def _fetch_state(self, state_dict):
        self.state.state_update(state_dict)
        state = self.filter_observations(self.state)
        filtered_state_dict = state.as_dict()
        return filtered_state_dict

    def _get_log_data(self):
        return self.get_log_data()

    def _set_action_result(self, action_result):
        """ A function that the environment calls (similarly as the self.get_action method) to set the action_result of the
        action this agent decided upon.

        Note, that the result is given AFTER the action is performed (if possible).
        Hence it is named the self.previous_action_result, as we can read its contents when we should decide on our
        NEXT action after the action whose result this is.

        Note; This method should NOT be overridden!

        Parameters
        ----------
        action_result : ActionResult
            An object that inherits from ActionResult, containing a boolean whether the action succeeded and a string
            denoting the reason why it failed (if it did so).
        """
        self.previous_action_result = action_result

    def _set_rnd_seed(self, seed):
        """ The function that seeds this agent's random seed.

        Note; This method should NOT be overridden!

        Parameters
        ----------
        seed : int
            The random seed this agent needs to be seeded with.
        """
        self.rnd_seed = seed
        self.rnd_gen = np.random.RandomState(self.rnd_seed)

    def _get_messages(self, all_agent_ids):
        """ Retrieves all message objects the agent has made in a tick, and returns those to the GridWorld for sending.
        It then removes all these messages!

        This method is called by the GridWorld.

        Note; This method should NOT be overridden!
        Parameters
        ----------
        all_agent_ids
            IDs of all agents

        Returns
        -------
            A list of message objects with a generic content, the sender (this agent's id) and optionally a
            receiver.
        """
        # # preproccesses messages such that they can be understand by the gridworld
        # preprocessed_messages = self.preprocess_messages(this_agent_id=self.agent_id, agent_ids=all_agent_ids,
        # messages=self.messages_to_send)

        send_messages = copy.copy(self.messages_to_send)

        # Remove all messages that need to be send, as we have send them now
        self.messages_to_send = []

        return send_messages

    def _set_messages(self, messages=None):
        """
        This method is called by the GridWorld.
        It sets all messages intended for this agent to a list that it can access and read.

        Note; This method should NOT be overridden!

        Parameters
        ----------
        messages : Dict (optional, default, None)
            A list of dictionaries that contain a 'from_id', 'to_id' and 'content. If messages is set to None (or no
            messages are used as input), only the previous messages are removed
        """

        # We empty all received messages as this is from the previous tick
        # self.received_messages = []

        # Loop through all messages and create a Message object out of the dictionaries.
        for mssg in messages:

            # Check if the message is of type Message (its content contains the actual message)
            AgentBrain.__check_message(mssg, self.agent_id)

            # Since each message is secretly wrapped inside a Message (as its content), we unpack its content and
            # set that as the actual received message.
            received_message = mssg.content

            # Add the message object to the received messages
            self.received_messages.append(received_message)

    def _init_state(self):
        self._state = State(memorize_for_ticks=self.memorize_for_ticks,
                            own_id=self.agent_id)

    @staticmethod
    def __check_message(mssg, this_agent_id):
        if not isinstance(mssg, Message):
            raise Exception(f"A message to {this_agent_id} is not, nor inherits from, the class {Message.__name__}."
                            f" This is required for agents to be able to send and receive them.")
