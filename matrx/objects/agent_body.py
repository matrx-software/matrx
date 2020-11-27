from matrx.agents.capabilities.capability import SenseCapability
from matrx.actions.action import Action
from matrx.objects.env_object import EnvObject


class AgentBody(EnvObject):
    """This class is a representation of an agent's body in the GridWorld.

    It is used as a measure to keep the AgentBrain code and Environment code separate. This AgentBody is used by
    the environment to update the GUI, perform actions, and update properties. It is kept in sync with the Agent's
    brain every iteration.

    It inherits from EnvObject which allows you set any custom properties you want. In addition it also has all the
    mandatory properties of an EnvObject plus a few extra. Which is the team name the agent is part of (if any) and
    what the Agent's body is carrying.

    In addition the Agent's body keeps a set of callbacks to methods inside the Agent. This forms the connection
    between the GridWorld (that calls them) and the Agent (that defined them).

    Parameters
    ----------
    location: List or tuple of length two.
        The location of the Agent's body in the grid world.
    possible_actions: list
        The list of Action class names this agent may be able to perform. This allows you to create agents that can
        only perform a couple of the available actions.
    sense_capability: The SenseCapability object.
    class_callable: Agent class
        The Agent class; in other words, the class of the agent's brain. This is stored here so that the Visualizer
        (which visualizes an agent based on this Agent's body object) and agents knows what kind of agent
        it is. Allows you to visualize certain agent types in a certain way.

    callback_agent_get_action: function
        The callback function as defined by the Agent instance of which this is an Agent's body of. It is called each
        tick by the GridWorld. As such the GridWorld determines when the Agent can
        perform an action by calling this function which is stored in the Agent's Agent's body.
    callback_agent_set_action_result: function
        Same as the callback_get_action but is used by GridWorld to set the
        ActionResult object in the Agent after performing the action. This allows the Agent to know how its planned
        action went.
    callback_agent_observe: function
        Similar to callback_agent_get_action, is used by GridWorld to obtain the
        processed state dictionary of the Agent. As the GridWorld does not know exactly what the Agent is allowed to
        see or not, the 'observe' preprocesses the given state further. But to accurately visualize what the agent sees
        we have to obtain that pre-processed state, which is done through this callback.
    callback_agent_initialize: function
        Call the initialize function in an Agent's Brain. Is done at the initialize
        of a GridWorld.

    callback_agent_get_messages: function
        A callback function that allows the GridWorld to obtain the agent's messages
        that need to be send to different agents.
    callback_agent_set_messages: function
        A callback function that allows the GridWorld to set any message send by
        some agent to a list of received messages in an agent.

    callback_create_context_menu_for_other: function
        A callback function that allows the gridworld or API to call the
        subsequent agent function that generates the menu options of an agent for a context menu opened by a user not
        controlling that specific agent.
    callback_create_context_menu_for_self: function
        A callback function that allows the gridworld or API to call the
        subsequent agent function that generates the menu options for a context menu opened by the user controlling
        the current human agent. If this is not a human agent, it is set to None.

    name: string. Optional, default="Agent"
        Defaults to "Agent". The name of the agent, does not need to be unique.
    is_human_agent: Boolean. Optional, default=False.
        Boolean to signal that the agent represented by this Agent's
        body is a human controlled agent.
    customizable_properties: List. Optional, default=obtained from defaults.py.
        The list of attribute names
        that can be customized by other objects (including Agent's body and as an extension any Agent).
    is_traversable: Boolean. Optional, default obtained from defaults.py.
        Signals whether other objects can be placed on top of this object.
    carried_by: List. Optional, default obtained from defaults.py.
        A list of who is carrying this object.
    team: string. Optional, default is ID of agent
        The team name the agent is part of.
        Defaults to the team name similar to the Agent's body unique
        ID, as such denoting that by default each Agent's body belongs to its own team and as an extension so does its
        "brain" the Agent.

    visualize_size: Float. Optional, default obtained from defaults.py.
        A visualization property used by
        the Visualizer. Denotes the size of the object, its unit is a single grid square in the visualization (e.g. a
        value of 0.5 is half of a square, object is in the center, a value of 2 is twice the square's size centered on
        its location.)
    visualize_shape: Int. Optional, default obtained from defaults.py.
        A visualization property used by the
        Visualizer. Denotes the shape of the object in the visualization.
    visualize_colour: Hexcode string. Optional, default obtained from defaults.py.
        A visualization property used by the Visualizer. Denotes the
    visualize_depth: Integer. Optional, default obtained from defaults.py.
        A visualization property that s used by the Visualizer to draw objects in layers.
    visualize_opacity: Integer.
        Opacity of object. Between 0.0 and 1.0.
    visualize_when_busy: Boolean.
        Whether to show a loading icon when the agent is busy (performing an action).
    **custom_properties: dict, optional
        Any other keyword arguments. All these are treated as custom attributes.
        For example the property 'heat'=2.4 of an EnvObject representing a fire.
    """

    def __init__(self, location, possible_actions, sense_capability, class_callable,
                 callback_agent_get_action, callback_agent_set_action_result, callback_agent_observe,
                 callback_agent_get_messages, callback_agent_set_messages, callback_agent_initialize,
                 callback_agent_log, callback_create_context_menu_for_other, callback_create_context_menu_for_self,
                 visualize_size, visualize_shape, visualize_colour, visualize_depth, visualize_opacity,
                 visualize_when_busy, is_traversable, team, name, is_movable,
                 is_human_agent, customizable_properties,
                 **custom_properties):

        # A list of EnvObjects or any class that inherits from it. Denotes all objects the Agent's body is currently
        # carrying. Note that these objects do not exist on the WorldGrid anymore, so removing them in this list deletes
        # them permanently.
        self.is_carrying = []  # list of EnvObjects that this object carries

        # The property that signals whether the agent this Agent's body represents is a human agent
        self.is_human_agent = is_human_agent

        # Save the other attributes the GridWorld expects an Agent's body to have access to an Agent's brain
        self.get_action_func = callback_agent_get_action
        self.set_action_result_func = callback_agent_set_action_result
        self.filter_observations = callback_agent_observe
        self.get_messages_func = callback_agent_get_messages
        self.set_messages_func = callback_agent_set_messages
        self.get_log_data = callback_agent_log
        self.brain_initialize_func = callback_agent_initialize
        self.create_context_menu_for_other_func = callback_create_context_menu_for_other
        self.create_context_menu_for_self_func = callback_create_context_menu_for_self

        # Set all mandatory properties
        self.is_traversable = is_traversable
        self.sense_capability = sense_capability
        self.action_set = possible_actions
        self.is_movable = is_movable

        # Set visualization properties
        self.visualize_depth = visualize_depth
        self.visualize_colour = visualize_colour
        self.visualize_shape = visualize_shape
        self.visualize_size = visualize_size
        self.visualize_opacity = visualize_opacity
        self.visualize_when_busy = visualize_when_busy

        # Parse the action_set property if set to the wildcard "*" denoting all actions
        if self.action_set == "*":
            self.action_set = list(_get_all_classes(Action, omit_super_class=True).keys())

        # Defines an agent is blocked by an action which takes multiple time steps. Is updated based on the speed with
        # which an agent can perform actions.
        self.__is_blocked = False

        # Place holders for action information
        self.__current_action = None
        self.__current_action_args = None

        # Denotes the last action performed by the agent, at what tick and how long it must take. Set to -infinite, such
        # that the agent is not deemed 'busy' at tick 0. Edit: changed from -inf to 1000000, to be JSON serializable
        self.__last_action_duration_data = {"duration_in_ticks": -1000000, "tick": -1000000, "action_name": None,
                                            "action_result": None}

        # We set a placeholder for the 'team' property so that it can be found in self.properties
        self.team = ""

        # Call the super constructor (we do this here because then we have access to all of EnvObject, including a
        # unique id
        super().__init__(location, name, customizable_properties=customizable_properties, is_traversable=is_traversable,
                         class_callable=class_callable,
                         visualize_size=visualize_size, visualize_shape=visualize_shape,
                         visualize_colour=visualize_colour, visualize_depth=visualize_depth,
                         visualize_opacity=visualize_opacity,
                         **custom_properties)

        # the GUI cannot differentiate capital letters (in the url), so make the agent ID lowercase
        self.obj_id = self.obj_id.lower()

        # If there was no team name given, the Agent's body (and as an extension its Agent's brain) is part of its own
        # team which is simply its object id + "_team". For this we need the object id, which was made in the EnvObject
        # constructor, that is why we call this AFTER calling that.
        if team is None:
            self.team = self.obj_id + "_team"
        self.change_property("team", self.team)

    def _set_agent_busy(self, curr_tick, action_duration):
        """
        specify the duration of the action in ticks currently being executed by the
        agent, and its starting tick
        """
        self.__last_action_duration_data = {"duration_in_ticks": action_duration, "tick": curr_tick}

    def _check_agent_busy(self, curr_tick):
        """
        check if the agent is done with executing the action
        """
        self.__is_blocked = curr_tick <= (self.current_action_tick_started + self.current_action_duration_in_ticks)

        return self.__is_blocked

    def _at_last_action_duration_tick(self, curr_tick):
        """ Returns True if this agent is at its last tick of the action's duration."""
        is_last_tick = curr_tick == (self.current_action_tick_started + self.current_action_duration_in_ticks)
        return is_last_tick

    def _get_duration_action(self):
        """ Returns the action we are waiting for 'self.current_action_duration_in_ticks', gets called in the GridWorld
        when we are at the last tick on which we should wait (see self._at_last_action_duration_tick)."""
        action_name = self.current_action
        action_kwargs = self.current_action_args

        return action_name, action_kwargs

    def _set_current_action(self, action_name, action_args):
        """
        Sets the current action of the agent. Since the GridWorld performs the mutate of an action first, and then waits
        for the duration to pass, we also have the result available.
        """
        self.__current_action = action_name
        self.__current_action_args = action_args

    def _set_agent_changed_properties(self, props: dict):
        """
        The Agent has possibly changed some of its properties during its OODA loop. Here the agent properties are also
        updated in the Agent's body, if it is allowed to change them as defined in 'customizable_properties' list.
        """
        # get all agent properties of this Agent's body in one dictionary
        body_properties = self.properties

        # check for each property if it has been changed by the agent, and if we need
        # to update our local copy (here in Agent's body) of the agent properties to match that
        for prop in props.keys():
            if prop not in body_properties.keys():
                raise Exception(f"Agent {self.obj_id} tried to remove the property {prop}, which is not allowed.")

            # check if the property has changed, and skip if not the case
            if props[prop] == body_properties[prop]:
                continue

            # if the agent has changed the property, check if the agent has permission to do so
            if prop not in self.customizable_properties:
                raise Exception(f"Agent {self.obj_id} tried to change a non-writable property: {prop}.")

            # The agent changed the property and the agent had permission to do so
            # update special properties
            self.change_property(prop, props[prop])

    def change_property(self, property_name, property_value):
        """
        Changes the value of an existing (!) property.

        Parameters
        ----------
        property_name: string
            The name of the property.
        property_value:
            The value of the property.

        Returns
        ----------
        The new properties
        """

        # We check if it is a custom property and if so change it simply in the dictionary
        if property_name in self.custom_properties.keys():
            self.custom_properties[property_name] = property_value
        else:  # else we need to check if property_name is a mandatory class attribute that is also a property
            if property_name == "is_traversable":
                assert isinstance(property_value, bool)
                self.is_traversable = property_value
            elif property_name == "name":
                assert isinstance(property_value, str)
                self.obj_name = property_value
            elif property_name == "location":
                assert isinstance(property_value, list) or isinstance(property_value, tuple)
                self.location = property_value
            elif property_name == "class_inheritance":
                assert isinstance(property_value, list)
                self.class_inheritance = property_value
            elif property_name == "visualize_size":
                assert isinstance(property_value, int)
                self.visualize_size = property_value
            elif property_name == "visualize_colour":
                assert isinstance(property_value, str)
                self.visualize_colour = property_value
            elif property_name == "visualize_opacity":
                assert isinstance(property_value, int)
                self.visualize_opacity = property_value
            elif property_name == "visualize_when_busy":
                assert isinstance(property_value, bool)
                self.visualize_when_busy = property_value
            elif property_name == "visualize_shape":
                assert isinstance(property_value, int)
                self.visualize_shape = property_value
            elif property_name == "visualize_depth":
                assert isinstance(property_value, int)
                self.visualize_depth = property_value
            elif property_name == "team":
                assert isinstance(property_value, str)
                self.team = property_value
            elif property_name == "sense_capability":
                assert isinstance(property_value, SenseCapability)
                self.sense_capability = property_value
            elif property_name == "is_human_agent":
                assert isinstance(property_value, bool)
                self.is_human_agent = property_value
            elif property_name == "action_set":
                assert isinstance(property_value, list)
                self.action_set = property_value
            elif property_name == "is_movable":
                assert isinstance(property_value, bool)
                self.is_movable = property_value
            # We deliberately ignore the current_action property, and several others such as agent_id as these can never
            # be altered as they are governed by the GridWorld

        return self.properties

    @property
    def location(self):
        """
        We override the location. Pythonic property here so we can override its setter.

        Returns
        -------
        Location: tuple
            The location tuple of the form; (x, y).
        """
        return tuple(self.__location)

    @location.setter
    def location(self, loc):
        """
        Overrides the setter of the location (pythonic) property so we can transfer also all carried objects with us
        on any location change made anywhere.
        Parameters
        ----------
        loc: tuple
            The new location
        """
        assert isinstance(loc, list) or isinstance(loc, tuple)
        assert len(loc) == 2
        # Set the location to our private location xy list
        self.__location = loc

        # Carrying action is done here
        # First we check if we even have a 'carrying' property, as the future might hold an Agent's body who
        # specifically removes this property. In that case we return.
        if 'carrying' not in self.properties.keys():
            return
        # Next we retrieve whatever it is the Agent's body is carrying (if we have a 'carrying' property at all)
        carried_objs = self.properties['carrying']
        # If we carry nothing, we are done
        if len(carried_objs) == 0:
            return
        # Otherwise we loop over all objects and adjust their location accordingly (since these are also EnvObjects,
        # their setter for location gets called, in the case we are carrying an Agent's body this setter is called
        for obj in carried_objs:
            obj.location = loc  # this requires all objects in self.properties['carrying'] to be of type EnvObject

    @property
    def properties(self):
        """
        Returns the custom properties of this object, but also any mandatory properties such as location, name,
        is_traversable and all visualization properties (those are in their own dictionary under 'visualization').

        In the case we return the properties of a class that inherits from EnvObject, we check if that class has

        Returns
        -------
        Properties: dict
            All mandatory and custom properties in a dictionary.
        """

        # Copy the custom properties
        properties = self.custom_properties.copy()

        # Add all mandatory properties. Make sure that these are updated if one are added to the constructor!
        properties['team'] = self.team
        properties['name'] = self.obj_name
        properties['obj_id'] = self.obj_id  # we return id as well, but this should never ever be modified!
        properties['location'] = self.location
        properties['is_movable'] = self.is_movable
        properties['action_set'] = self.action_set
        properties['carried_by'] = self.carried_by
        properties['is_human_agent'] = self.is_human_agent
        properties['is_traversable'] = self.is_traversable
        properties['class_inheritance'] = self.class_inheritance
        properties['is_blocked_by_action'] = self.is_blocked
        properties['is_carrying'] = [obj.properties for obj in self.is_carrying]
        properties['sense_capability'] = self.sense_capability.get_capabilities()
        properties['visualization'] = {
            "size": self.visualize_size,
            "shape": self.visualize_shape,
            "colour": self.visualize_colour,
            "depth": self.visualize_depth,
            "opacity": self.visualize_opacity,
            "show_busy": self.visualize_when_busy
        }

        # Add the current action and all of its data
        properties['current_action'] = self.current_action
        if self.current_action is not None:  # all None actions are 'idle' actions and have no name or result
            properties['current_action_args'] = self.current_action_args  # the action arguments
        else:
            properties['current_action_args'] = {}

        properties['current_action_duration'] = self.current_action_duration_in_ticks
        properties['current_action_started_at_tick'] = self.current_action_tick_started

        return properties

    @properties.setter
    def properties(self, property_dictionary: dict):
        """
        Here to protect the 'properties' variable. It does not do anything and should not do anything!
        """
        pass

    @property
    def current_action(self):
        return self.__current_action

    @property
    def current_action_duration_in_ticks(self):
        return self.__last_action_duration_data["duration_in_ticks"]

    @property
    def current_action_tick_started(self):
        return self.__last_action_duration_data["tick"]

    @property
    def current_action_args(self):
        return self.__current_action_args

    @property
    def is_blocked(self):
        return self.__is_blocked


def _get_all_classes(class_, omit_super_class=False):
    # Include given class or not
    if omit_super_class:
        subclasses = set()
    else:
        subclasses = {class_}

    # Go through all child classes
    work = [class_]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)

    # Create a dict out of it
    act_dict = {}
    for action_class in subclasses:
        act_dict[action_class.__name__] = action_class

    return act_dict
