

class Action:

    def __init__(self, name, duration_in_ticks = 1):
        """
        The core action class. This class is empty and should be overridden if you want to make a new action that is not
        yet supported. You may also extend other actions, as long as their super class is this class.

        The two methods you should override are;
        - mutate; performs the actual mutation on the grid world
        - is_possible; checks whether the action can be performed in the first place.

        :param name: The name of the action. By default this should be the class name. Hence you should assign this in
        the constructor of your custom action class to;
        `name = self.__class__`
        :param duration: The duration of the action. By default this is 1. For an action which takes multiple ticks and
        blocks the user, you should assign a custom duration in the constructor of your custom action class.

        """
        self.name = name
        # number of ticks the action takes to complete
        self.duration_in_ticks = duration_in_ticks

    def mutate(self, grid_world, agent_id, **kwargs):
        """
        The core of an action. This method needs to be overridden and performs the actual action in the world.
        As such the mutate receives the entire world as a pointer, the agent_id who performs the action and potential
        keyword arguments unique for a specific action (e.g., an object id for the RemoveObject action).

        The mutate should always return an ActionResult, or a class that inherits from ActionResult.

        The mutate will only be called when action.is_possible(...) returns True. The grid world is responsible for
        translating an agent's returned action class name, to an action object, check if it is a possible action and
        then call this mutate method.

        :param grid_world: A pointer to the actual world object.
        :param agent_id: The id known in the grid world as an agent that peforms this action.
        :param kwargs: Optional arguments for the action. You should document what these arguments are in your Python
        doc, and ALWAYS check whether these are present and otherwise raise an exception! This eases the debugging
        process for everyone. This check can be done in the is_possible method of the action. If done there, it can be
        omitted here since that method is always called before mutate.
        :return: An action result depicting the action's success or failure and reason/description of that result.
        """
        pass

    def is_possible(self, grid_world, agent_id, **kwargs):
        """
        Checks whether the action is possible in the world when performed by the given agent. This method needs to be
        overridden, to perform this check for the action you want to implement. It returns a boolean stating whether
        the action can be performed (True) or not (False).

        If the action requires any optional arguments, this method only checks whether SOME instantation of this action
        is possible. So for example the RemoveObject action, would check if there is just one object in the entire grid
        that could be removed. If so, the action is possible although when you state the object_id to be removed and
        the range in which this can happen it might occur that the object is not there or not within range, still
        resulting in a failure with an ActionResult telling you the reason.

        The environment will call this method to check whether the action's mutate method should be called or not.
        Hence, if you notice that your action is never being performed on the world, it might be that this method
        always returns False.

        It should also return a second argument, stating why an action was failed. This is used in the ActionResult. If
        the action is possible, this string is ignored and can simply be None. If the string is None and the action is
        not possible, the world would use the default ActionResult.ACTION_NOT_POSSIBLE message. This string allows you
        to signal to an agent the exact reason why an action was failed, which the agent may or may not choose to use
        depending on your agent implementation.

        :param grid_world: A pointer to the actual world object.
        :param agent_id: The id known in the grid world as an agent that peforms this action.
        :return: Returns two things; a boolean signalling whether the action is possible or not, and a string telling
        you why the action was not possible. This string is used to fill the ActionResult when the boolean was False
        (signalling that the action is not possible). If the string is None, the default message for an impossible
        action is used in the ActionResult. If the action is possible (the boolean is True), this string is ignored.
        """
        pass


class ActionResult:

    AGENT_WAS_REMOVED = "Agent {AGENT_ID} was removed during this tick, cannot perform anymore actions."
    ACTION_SUCCEEDED = "The action succeeded."
    ACTION_NOT_POSSIBLE = "The `is_possible(...)` method returned False. Signalling that the action was not possible."
    AGENT_NOT_CAPABLE = "The action could not be performed, as the agent is not capable of performing this action."
    UNKNOWN_ACTION = "The action is not known to the environment."
    NO_ACTION_GIVEN = "There was no action given to perform, automatic succeed."

    def __init__(self, result, succeeded):
        self.result = result
        self.succeeded = succeeded
