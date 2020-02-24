

class Action:
    """ The Action class.

    This class is empty and should be overridden if you want to make a new action that is not yet supported. You may
    also extend other actions, but all MATRX' actions inherit from this class.

    When creating a new Action, you should always override the Action.mutate(...) and Action.is_possible(...)
    methods.

    Parameters
    ----------
    duration_in_ticks : int
        The default duration of the action in ticks during which the GridWorld blocks the Agent performing other
        actions. By default this is 1, meaning that the action will take both the tick in which it was decided upon
        and the subsequent tick. When creating your own Action, you can override this default value. Should be zero
        or positive.

    See Also
    --------
    mutate : performs the actual mutation on the GridWorld
    is_possible : returns whether the action can be performed.

    Notes
    -----
    The duration_in_ticks only represents the default duration of an Action. It can be overridden at any time by the
    AgentBrain with another value.

    """

    def __init__(self, duration_in_ticks=1):
        # number of ticks the action takes to complete
        self.duration_in_ticks = duration_in_ticks

    def mutate(self, grid_world, agent_id, **kwargs):
        """ Method that mutates GridWorld.

        This method receives a GridWorld instance and is allowed to mutate it according to the Action's purposes.
        Override this method when implementing a new Action. It will be called by the GridWorld iff:
        - An AgentBrain selected this action.
        - The implemented is_possible(...) method returned True.
        - The action_duration has passed.
        - The Agent is not busy with another action.
        - It is not the Agent's turn to take an action.
        Hence, this method is not required to make these checks first.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance that should be mutated according to the Action's intended purpose.
        agent_id : string
            The unique identifier of the agent performing this action.
        kwargs : dictionary
            The set of keyword arguments provided by the Agent that decided upon this action. When overriding this
            method and setting required arguments, the GridWorld will take responsibility in checking whether the Agent
            provided these. Hence, it is not required to do so here.

        Returns
        -------
        ActionResult
            An instance of the ActionResult class, or an inherited class thereof, which denotes whether the mutation
            actually succeeded or not, together with the reason why not. This result is passed to the agent by the
            GridWorld instance so that an Agent is capable of checking when and why an Action succeeded or failed.

        Warnings
        --------
        It is important to remember that the given GridWorld instance, represents the actual world. Any change to this
        instance are immediately reflected in the world, agent states and potential visualisations.

        See Also
        --------
        GridWorld : Contains additional functions to make the implementation of Actions simpler.
        ActionResult : Contains a description on how to create an ActionResult.

        """
        return None

    def is_possible(self, grid_world, agent_id, **kwargs):
        """ Checks if the Action is possible

        This method receives the GridWorld instance to check whether the Action is possible to perform. Override this
        method when implementing a new Action. It will be called by the GridWorld iff:
        - An AgentBrain selected this action.
        - The Agent is not busy with another action.
        - It is not the Agent's turn to take an action.
        OR
        - An AgentBrain requested if a certain Action is possible. (Requested functionality: See Issue #46)

        It is important to understand that this function does not have to guarantee the success of an Action. It might
        be impossible to check if an Action would always succeed without actually performing the mutation. Hence, this
        method only needs to check for general cases if the Action would succeed. The Action.mutate(...) itself also
        returns an ActionResult which denotes the actual success or failure of the Action.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance that should be used to check if this Action is possible.
        agent_id : string
            The unique identifier of the agent performing this action.
        kwargs : dictionary
            The set of keyword arguments provided by the Agent that decided upon this action. When overriding this
            method and setting required arguments, the GridWorld will take responsibility in checking whether the Agent
            provided these. Hence, it is not required to do so here.

        Returns
        -------
        ActionResult
            The expected ActionResult when performing this Action. The ActionResult.succeeded attribute is used to check
            if the Action is indeed possible by the GridWorld.

        Warnings
        --------
        It is important to remember that the given GridWorld instance, represents the actual world. This method should
        not change anything in this instance. This is reserved for the Action.mutate(...) method as any change here will
        be reflected in the world, agent states and potential visualisations.

        See Also
        --------
        GridWorld : Contains additional functions to make the implementation of Actions simpler.
        ActionResult : Contains a description on how to create an ActionResult.

        """
        return None


class ActionResult:

    IDLE_ACTION = "The action is None, hence the agent will idle which always succeeds."
    AGENT_WAS_REMOVED = "Agent {AGENT_ID} was removed during this tick, cannot perform anymore actions."
    ACTION_SUCCEEDED = "The action succeeded."
    ACTION_NOT_POSSIBLE = "The `is_possible(...)` method returned False. Signalling that the action was not possible."
    AGENT_NOT_CAPABLE = "The action could not be performed, as the agent is not capable of performing this action."
    UNKNOWN_ACTION = "The action is not known to the environment."
    NO_ACTION_GIVEN = "There was no action given to perform, automatic succeed."

    def __init__(self, result, succeeded):
        """ Represents the (expected) result of an Action.

        This class functions as a simple wrapper around a boolean representing the success (True) or failure (False) of
        an Action's (expected) mutation, as well as the reason for it. Both the methods  Action.is_possible(...) and
        Action.mutate(...) return an ActionResult. With the former it represents the expected success or failure of the
        Action, with the latter the actual success or failure.

        The ActionResult class contains several generic reasons for a succeed or fail as constant attributes. These
        reasons can be used by any custom made Action, or a new reason for the result can be given. You can also extend
        this class with your own, which should only contain a custom set of constants representing reasons for that
        Action's specific results. This has the advantage that an AgentBrain can directly match the ActionResult.result
        with such a class constant.

        Some ActionResult reasons are only used by the GridWorld. These are as follows:
        ActionResult.IDLE_ACTION :          Always given when an AgentBrain decided upon returning None (the idle
                                            action)
        ActionResult.AGENT_WAS_REMOVED :    Always given when an agent does not exist anymore in the GridWorld.
        ActionResult.AGENT_NOT_CAPABLE :    Always given when the Action an AgentBrain decided upon is not an Action
                                            that  agent should be capable of.
        ActionResult.UNKNOWN_ACTION :       Always given when the Action name an AgentBrain decided upon is not
                                            recognized as a class name of an Action or some class inheriting from
                                            Action. Could be caused by either that class not existing or because it
                                            is never imported anywhere (and hence is not on the path the GridWorld
                                            searches in).

        Parameters
        ----------
        result : string
            A string representing the reason for an Action's (expected) success or fail.
        succeeded : boolean
            A boolean representing the (expected) success or fail of an Action.

        See Also
        --------
        Action : The super-class whose children return an ActionResult

        """

        self.result = result
        self.succeeded = succeeded
