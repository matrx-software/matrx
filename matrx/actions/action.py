""" Main module for the core's Action class.
"""


class Action:
    """ Contains the effects of an action on the world.

    This class is empty and should be overridden if you want to make a
    new action that is not yet supported. You may also extend other
    actions, but all MATRX' actions inherit from this class.

    Parameters
    ----------
    duration_in_ticks : int
        The default duration of the action in ticks during which the
        GridWorld blocks the Agent performing other actions. By default
        this is 1, meaning that the action will take both the tick in which
        it was decided upon and the subsequent tick. When creating your
        own Action, you can override this default value.

    """

    def __init__(self, duration_in_ticks=0):
        # number of ticks the action takes to complete
        self.duration_in_ticks = duration_in_ticks

    def mutate(self, grid_world, agent_id, **kwargs):
        """ Method that mutates the world.

        This method is allowed to mutate a :class:`matrx.grid_world.GridWorld`
        instance according to the purposes of the
        :class:`matrx.actions.Action`. Override this method when implementing
        a new :class:`matrx.actions.action.Action`.

        Parameters
        ----------
        grid_world
            The GridWorld instance that should be mutated according to the
            Action's intended purpose.
        agent_id : string
            The unique identifier of the agent performing this action.
        **kwargs
            The set of keyword arguments provided by the agent that decided
            upon this action. When overriding this method and setting required
            arguments, the :class:`matrx.grid_world.GridWorld` will take
            responsibility in checking whether the agent provided these. Hence,
            it is not required to do so here.

        Returns
        -------
        ActionResult
            An instance of the :class:`matrx.actions.Action.ActionResult`
            class, or an inherited class thereof, which denotes whether the
            mutation actually succeeded or not, together with the reason why.
            This result is passed to the
            :class:`matrx.agents.agent_brain.AgentBrain` by the
            :class:`matrx.grid_world.GridWorld` instance so that an agent is
            capable of checking when and why an
            :class:`matrx.actions.action.Action` succeeded or failed.

        Notes
        -----
        This method is called by the :class:`matrx.grid_world.GridWorld` iff:

        * An :class:`matrx.agents.agent_brain.AgentBrain` of an agent decided
          upon this action.
        * It is the turn of the agent to take an action.
        * The implemented :meth:`matrx.actions.Action.is_possible` method
          returned an :class:`matrx.actions.Action.ActionResult.succeeded`
          denoting success.
        * The `action_duration` has passed.

        Furthermore, it is important to remember that the given
        :class:matrx.grid_world.GridWorld` instance, represents the actual
        world. Any change to this instance are immediately reflected in the
        world.

        See Also
        --------
        matrx.grid_world.GridWorld :
            Contains additional functions to make the implementation of
            :class:`matrx.actions.action.Action` simpler.
        ActionResult :
            Contains a description on how to create an instance of
            :class:`matrx.actions.action.ActionResult`, or how to override it
            for your own custom :class:`matrx.actions.action.Action`.

        """
        return None

    def is_possible(self, grid_world, agent_id, **kwargs):
        """ Checks if the Action is possible.

        This method analyses a :class:`matrx.grid_world.GridWorld` instance
        to check if the Action is possible to perform. Override this method
        when implementing a new :class:`matrx.actions.action.Action`.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance that should be used to check if this Action
            is possible.
        agent_id : string
            The unique identifier of the agent performing this action.
        kwargs : dictionary
            The set of keyword arguments provided by the Agent that decided
            upon this action. When overriding this method and setting required
            arguments, the GridWorld will take responsibility in checking
            whether the Agent provided these. Hence, it is not required to do
            so here.

        Returns
        -------
        ActionResult
            The expected :class:`matrx.actions.action.ActionResult` when
            performing this :class:`matrx.actions.action.Action`. The
            :attr:`matrx.actions.action.ActionResult.succeeded` attribute is
            used to check if the :class:`matrx.actions.action.Action` is
            indeed possible by the :class:`matrx.grid_world.GridWorld`.

        Notes
        -----
        It is important to understand that this function does not have to
        guarantee the success of an :class:`matrx.actions.action.Action`. It
        might be impossible to check if an
        :class:`matrx.actions.action.Action` would always succeed without
        actually performing the mutation. Hence, this method only needs to
        check for general cases. The
        :meth:`matrx.actions.action.Action.mutate` itself also returns an
        :class:`matrx.actions.action.ActionResult` which denotes the actual
        success or failure of the Action.

        This method is called by the :class:`matrx.grid_world.GridWorld` iff:

        * An :class:`matrx.agents.agent_brain.AgentBrain` of an agent decided
          upon this action.
        * It is the turn of the agent to take an action.
        * The `action_duration` has passed.

        OR

        * An :class:`matrx.agents.agent_brain.AgentBrain` requested if a
          certain :class:`matrx.actions.action.Action` is possible. (Requested
          functionality: See Issue #46)

        Warnings
        --------
        This method should not change anything in this instance. This is
        reserved for the :meth:`matrx.actions.action.Action.mutate` method as
        any change here will be reflected in the world.

        See Also
        --------
        GridWorld :
            Contains additional functions to make the implementation of Actions
            simpler.
        ActionResult :
            Contains a description on how to create an ActionResult.

        """
        return None


class ActionResult:
    """ Represents the generic (expected) result of an action.

    This class functions as a simple wrapper around a boolean representing the
    success (`True`) or failure (`False`) of the (expected) mutation of an
    :class:`matrx.actions.action.Action`, as well as the reason for it.

    The :class:`matrx.actions.action.ActionResult` class contains several
    generic reasons for a succeed or fail as constant class attributes.

    Parameters
    ----------
    result : str
        A string representing the reason for the (expected) success or fail of
        an :class:`matrx.actions.action.Action`.
    succeeded : bool
        A boolean representing the (expected) success or fail of an
        :class:`matrx.actions.action.Action`.

    Notes
    -----
    Both the methods :meth:`matrx.actions.Action.is_possible` and
    :meth:`matrx.actions.Action.mutate` should return an
    :class:`matrx.actions.action.ActionResult`. With the former it represents
    the expected success or failure of the
    :class:`matrx.actions.action.Action`, with the latter the actual success
    or failure.

    The :class:`matrx.actions.action.ActionResult` class contain several
    reasons why an :class:`matrx.actions.action.Action` may succeed or fail
    that are being checked by a :class:`matrx.grid_world.GridWorld` instance.
    These are:

        * IDLE_ACTION: Always given when an AgentBrain decided upon returning
          None (the idle action)
        * AGENT_WAS_REMOVED: Always given when an agent does not exist anymore
          in the GridWorld.
        * AGENT_NOT_CAPABLE: Always given when the Action an AgentBrain decided
          upon is not an Action that agent
          should be capable of.
        * UNKNOWN_ACTION: Always given when the Action name an AgentBrain
          decided upon is not recognized as a class name of an Action or some
          class inheriting from Action. Could be caused by either that class
          not existing or because it is never imported anywhere (and hence is
          not on the path the GridWorld searches in).

    When creating a new :class:`matrx.actions.action.Action` class, you can
    also extend this class with your own. This allows you to set your own
    constants representing reasons for that
    :class:`matrx.actions.action.Action` specific results. This allows an
    :class:`matrx.agents.agent_brain.AgentBrain` to directly match the
    :attr:`matrx.actions.ActionResult.result` with a constant and potentially
    adjust its behavior.

    See Also
    --------
    Action : The super-class whose children return an ActionResult

    """

    """ Result string for when the action is None. """
    IDLE_ACTION = "The action is None, hence the agent will idle which " \
                  "always succeeds. "

    """ Result string for when the agent was removed before performing 
    its action. """
    AGENT_WAS_REMOVED = "Agent {AGENT_ID} was removed during this tick, " \
                        "cannot perform anymore actions. "

    """ Result when the action succeeded or is expected to succeed."""
    ACTION_SUCCEEDED = "The action succeeded."

    """ Result when the action is not expected to succeed. """
    ACTION_NOT_POSSIBLE = "The `is_possible(...)` method returned False. " \
                          "Signalling that the action was not possible. "

    """ Result when the agent is not capable of performing that action. """
    AGENT_NOT_CAPABLE = "The action could not be performed, as the agent is " \
                        "not capable of performing this action. "

    """ Result when the action name does not represent an ``Action`` class"""
    UNKNOWN_ACTION = "The action is not known to the environment."

    """ *Deprecated: Use IDLE_ACTION instead.* """
    NO_ACTION_GIVEN = "There was no action given to perform, automatic " \
                      "succeed. "

    def __init__(self, result, succeeded):
        self.result = result
        self.succeeded = succeeded
