from matrx.actions.action import Action, ActionResult
from matrx.objects.agent_body import AgentBody


def _act_move(grid_world, agent_id, dx, dy):
    """ Private MATRX method.

    The method that actually mutates the location of an AgentBody based on a
    delta-x and delta-y.

    Parameters
    ----------
    grid_world : GridWorld
        The GridWorld instance in which the agent resides whose location
        should be updated.
    agent_id : string
        The unique identifier for the agent whose location should be changed.
    dx : {-1, 0, 1}
        The delta change on the x-coordinate.
    dy : {-1, 0, 1}
        The delta change on the y-coordinate.

    Returns
    -------
    MoveActionResult
        The result of the actual change of the location of an AgentBody.
        Always returns a success.

    """
    agent_avatar = grid_world.get_env_object(agent_id, obj_type=AgentBody)
    loc = agent_avatar.location
    new_loc = [loc[0] + dx, loc[1] + dy]
    grid_world.registered_agents[agent_id].location = new_loc

    return MoveActionResult(MoveActionResult.RESULT_SUCCESS, succeeded=True)


def _is_possible_movement(grid_world, agent_id, dx, dy):
    """ Private MATRX method.

    Wrapper around the check if a certain movement is possible.

    Parameters
    ----------
    grid_world : GridWorld
        The GridWorld instance in which the agent resides whose location
        should be updated.
    agent_id : string
        The unique identifier for the agent whose location should be changed.
    dx : {-1, 0, 1}
        The delta change on the x-coordinate.
    dy : {-1, 0, 1}
        The delta change on the y-coordinate.

    Returns
    -------
    MoveActionResult
        The expected result of performing this movement.

    See Also
    --------
    possible_movement : The main method this method wraps.

    """
    return _possible_movement(grid_world, agent_id, dx, dy)


def _possible_movement(grid_world, agent_id, dx, dy):
    """ Private MATRX method.

    Checks if the delta-x and delta-y change in the agent's location is
    possible.

    Parameters
    ----------
    grid_world : GridWorld
        The GridWorld instance in which the agent resides whose location should
        be updated.
    agent_id : string
        The unique identifier for the agent whose location should be changed.
    dx : {-1, 0, 1}
        The delta change on the x-coordinate.
    dy : {-1, 0, 1}
        The delta change on the y-coordinate.

    Returns
    -------
    MoveActionResult
        Whether the MoveAction is expected to be possible.
        Can return the following results (see also
        :class:`matrx.actions.move_actions.MoveActionResult`):

        * The ActionResult depicting the action's success or failure and reason
          for that result.
        * RESULT_SUCCESS: When the MoveAction is possible.
        * RESULT_NO_MOVE: If the agent is already at the
          location it wishes to move to.
        * RESULT_OCCUPIED: When the new location is occupied
          by an intraversable agent.
        * RESULT_NOT_PASSABLE_OBJECT: When the new location is
          occupied by an intraversable object.
        * RESULT_OUT_OF_BOUNDS: When the new location is
          outside the GridWorld's bounds.

    """

    agent_avatar = grid_world.get_env_object(agent_id, obj_type=AgentBody)
    assert agent_avatar is not None

    loc = agent_avatar.location
    new_loc = [loc[0] + dx, loc[1] + dy]
    if 0 <= new_loc[0] < grid_world.shape[0] and 0 <= new_loc[1] < grid_world.shape[1]:
        loc_obj_ids = grid_world.grid[new_loc[1], new_loc[0]]
        if loc_obj_ids is None:
            # there is nothing at that location
            return MoveActionResult(MoveActionResult.RESULT_SUCCESS, succeeded=True)
        else:
            # Go through all objects at the desired locations
            for loc_obj_id in loc_obj_ids:
                # Check if loc_obj_id is the id of an agent
                if loc_obj_id in grid_world.registered_agents.keys():
                    # get the actual agent
                    loc_obj = grid_world.registered_agents[loc_obj_id]
                    # Check if the agent that takes the move action is not that agent at that location (meaning that
                    # for some reason the move action has no effect. If this is the case, we send the appropriate
                    # result
                    if loc_obj_id == agent_id:
                        # The desired location contains a different agent and we cannot step at locations with agents
                        return MoveActionResult(MoveActionResult.RESULT_NO_MOVE, succeeded=False)
                    # Check if the agent on the other location (if not itself) is traverable. Otherwise we return that
                    # the location is occupied.
                    elif not loc_obj.is_traversable:
                        return MoveActionResult(MoveActionResult.RESULT_OCCUPIED, succeeded=False)
                # If there are no agents at the desired location or we can move on top of other agents, we check if
                # there are objects in the way that are not passable.
                if loc_obj_id in grid_world.environment_objects.keys():
                    # get the actual object
                    loc_obj = grid_world.environment_objects[loc_obj_id]
                    # Check if the object is not passable, if this is not the case is_traversable is False
                    if not loc_obj.is_traversable:
                        # The desired location contains an object that is not passable
                        return MoveActionResult(MoveActionResult.RESULT_NOT_PASSABLE_OBJECT, succeeded=False)

        # Either the desired location contains the agent at previous tick, and/or all objects there are passable
        return MoveActionResult(MoveActionResult.RESULT_SUCCESS, succeeded=True)
    else:
        return MoveActionResult(MoveActionResult.RESULT_OUT_OF_BOUNDS, succeeded=False)


class MoveActionResult(ActionResult):
    """ActionResult for a Move action

    The results uniquely for Move action are (as class constants):

    * RESULT_SUCCESS: When the MoveAction is possible.
    * RESULT_NO_MOVE: If the agent is already at the location it wishes to move
      to.
    * RESULT_OCCUPIED: When the new location is occupied by an intraversable
      agent.
    * RESULT_NOT_PASSABLE_OBJECT: When the new location is occupied by an
      intraversable object.
    * RESULT_OUT_OF_BOUNDS: When the new location is outside the GridWorld's
      bounds.

    Parameters
    ----------
    result : str
        A string representing the reason for a (expected) success
        or fail of a :class:`matrx.actions.move_actions.Move`.
    succeeded : bool
        A boolean representing the (expected) success or fail of a
        :class:`matrx.actions.move_actions.Move`.

    See Also
    --------
    Move

    """

    """ When the move action is success. """
    RESULT_SUCCESS = 'Move action success'

    """ When the agent is already at the location it tries to move to. """
    RESULT_NO_MOVE = 'Move action resulted in a new location with the agent already present.'

    """ When the move action would lead the agent outside the world bounds. """
    RESULT_OUT_OF_BOUNDS = 'Move action out of bounds'

    """ When the move action would lead the agent to a location occupied by 
    another agent. """
    RESULT_OCCUPIED = 'Move action towards occupied space'

    """ When the move action would lead the agent to a location occupied by 
    an intraversable object. """
    RESULT_NOT_PASSABLE_OBJECT = 'Move action toward space which is not traversable by agent due object'

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)


class Move(Action):
    """ The class wrapping all Move actions.

    Parameters
    ----------
    duration_in_ticks : int
        Optional. Default: ``1``. Should be zero or larger.

        The default duration of Move in ticks during which the
        :class:`matrx.grid_world.GridWorld` blocks the agent performing other
        actions. By default this is 1, meaning that all Move actions will take
        both the tick in which it was decided upon and the subsequent tick.

    Attributes
    ----------
    dx : {-1, 0, 1}
        The delta change on the x-coordinate.
    dy : {-1, 0, 1}
        The delta change on the y-coordinate.

    See Also
    --------
    MoveNorth
    MoveNorthEast
    MoveEast
    MoveSouthEast
    MoveSouth
    MoveSouthWest
    MoveWest
    MoveNorthWest

    """

    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)
        self.dx = 0
        self.dy = 0

    def is_possible(self, grid_world, agent_id, **kwargs):
        """ Checks if the move is possible.

        Checks for the following:

        * If the agent is already at the location it wishes to move to.
        * When the new location is occupied by an intraversable agent.
        * When the new location is occupied by an intraversable object.
        * When the new location is outside the GridWorld's bounds.

        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            agent resides whose location should be updated.
        agent_id : str
            The unique identifier for the agent whose location should be
            changed.
        **kwargs : dict
            Not used.

        Returns
        -------
        MoveActionResult
            Whether the MoveAction is expected to be possible.

            See :class:`matrx.actions.move_actions.MoveActionResult` for the
            results it can contain.

        """
        result = _is_possible_movement(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)
        return result

    def mutate(self, grid_world, agent_id, **kwargs):
        """ Mutates an agent's location

        Changes an agent's location property based on the attributes `dx` and
        `dy`.

        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            agent resides whose location should be updated.
        agent_id : str
            The unique identifier for the agent whose location should be
            changed.

        Returns
        -------
        MoveActionResult
            The result of the actual change of the location of an agent. Always
            returns a success.

        """
        return _act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)


class MoveNorth(Move):
    """ Moves the agent North.

    Inherits from :class:`matrx.actions.move_action.Move` and sets the delta-x
    and delta-y as follows:

    * delta-x = 0
    * delta-y = -1

    See Also
    --------
    Move

    """

    def __init__(self):
        super().__init__()
        self.dx = 0
        self.dy = -1


class MoveNorthEast(Move):
    """ Moves the agent North-East.

    Inherits from :class:`matrx.actions.move_action.Move` and sets the delta-x
    and delta-y as follows:

    * delta-x = 1
    * delta-y = -1

    See Also
    --------
    Move

    """

    def __init__(self):
        super().__init__()
        self.dx = +1
        self.dy = -1


class MoveEast(Move):
    """ Moves the agent East.

    Inherits from :class:`matrx.actions.move_action.Move` and sets the delta-x
    and delta-y as follows:

    * delta-x = 1
    * delta-y = 0

    See Also
    --------
    Move

    """

    def __init__(self):
        super().__init__()
        self.dx = +1
        self.dy = 0


class MoveSouthEast(Move):
    """ Moves the agent South-East.

    Inherits from :class:`matrx.actions.move_action.Move` and sets the delta-x
    and delta-y as follows:

    * delta-x = 1
    * delta-y = 1

    See Also
    --------
    Move

    """

    def __init__(self):
        super().__init__()
        self.dx = +1
        self.dy = +1


class MoveSouth(Move):
    """ Moves the agent South.

    Inherits from :class:`matrx.actions.move_action.Move` and sets the delta-x
    and delta-y as follows:

    * delta-x = 0
    * delta-y = 1

    See Also
    --------
    Move

    """

    def __init__(self):
        super().__init__()
        self.dx = 0
        self.dy = +1


class MoveSouthWest(Move):
    """ Moves the agent South-West.

    Inherits from :class:`matrx.actions.move_action.Move` and sets the delta-x
    and delta-y as follows:

    * delta-x = -1
    * delta-y = 1

    See Also
    --------
    Move

    """

    def __init__(self):
        super().__init__()
        self.dx = -1
        self.dy = +1


class MoveWest(Move):
    """ Moves the agent West.

    Inherits from :class:`matrx.actions.move_action.Move` and sets the delta-x
    and delta-y as follows:

    * delta-x = -1
    * delta-y = 0

    See Also
    --------
    Move

    """

    def __init__(self):
        super().__init__()
        self.dx = -1
        self.dy = 0


class MoveNorthWest(Move):
    """ Moves the agent North-West.

    Inherits from :class:`matrx.actions.move_action.Move` and sets the delta-x
    and delta-y as follows:

    * delta-x = -1
    * delta-y = -1

    See Also
    --------
    Move

    """

    def __init__(self):
        super().__init__()
        self.dx = -1
        self.dy = -1
