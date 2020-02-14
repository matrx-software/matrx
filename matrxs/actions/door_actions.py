import numpy as np

from matrxs.actions.action import Action, ActionResult
from matrxs.objects.simple_objects import Door


class OpenDoorAction(Action):

    def __init__(self, duration_in_ticks=1):
        """ Action that opens doors.

        The action that opens a specific door within a given range from the agent.

        Parameters
        ----------
        duration_in_ticks : int
            The default duration of OpenDoorAction in ticks during which the GridWorld blocks the Agent performing other
            actions. By default this is 1, meaning that the OpenDoorAction will take both the tick in which it was
            decided upon and the subsequent tick. Should be zero or larger.

        """

        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, **kwargs):
        """ Opens a door in the world.

        Mutates a Door object's door_status in the GridWorld to be open (and as such passable). It does so only if the
        Door object id exists (given as the object_id parameter) and the Door is within range (which is 1 by default, or
        overridden by a door_range parameter).

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the door is sought according to the object_id parameter.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string
            The string representing the unique identifier of the door that should be opened.
        door_range : int (default=np.inf)
            The maximum allowed distance between the agent and the door for the agent to be able to open that door.

        Returns
        -------
        OpenDoorActionResult
            The ActionResult depicting the action's success or failure and reason for that result.
            Returns the following results:
            OpenDoorActionResult.NO_OBJECT_SPECIFIED    : When no object_id was given.
            OpenDoorActionResult.RESULT_SUCCESS         : When the door is opened.
        """

        # fetch options
        door_range = 1 if 'door_range' not in kwargs else kwargs['door_range']
        # object_id is required
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        if object_id == None:
            result = OpenDoorActionResult(OpenDoorActionResult.NO_OBJECT_SPECIFIED, False)
            return result

        # get obj
        obj = grid_world.environment_objects[object_id]

        # call the open door action in the object
        obj.open_door()

        result = OpenDoorActionResult(OpenDoorActionResult.RESULT_SUCCESS, True)
        return result

    def is_possible(self, grid_world, agent_id, **kwargs):
        """ Check if the OpenDoorAction is possible.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the door is sought according to the object_id parameter.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string
            The string representing the unique identifier of the door that should be opened.
        door_range : int (default=np.inf)
            The maximum allowed distance between the agent and the door for the agent to be able to open that door.

        Returns
        -------
        OpenDoorActionResult
            The ActionResult determining the expected result of an OpenDoorAction with the given parameters.
            Can return the following results:
            OpenDoorActionResult.NO_DOORS_IN_RANGE      : When no EnvObject of type Door are in range.
            OpenDoorActionResult.NOT_A_DOOR             : When the given object_id does not exist.
            OpenDoorActionResult.NOT_A_DOOR             : When the given object_id does not exist.
            OpenDoorActionResult.NOT_IN_RANGE           : When the given object_id it not within range.
            OpenDoorActionResult.DOOR_ALREADY_OPEN      : When the Door object is already open.
            OpenDoorActionResult.SUCCESS                : When the door can be successfully opened.

        """
        # fetch options
        door_range = np.inf if 'door_range' not in kwargs else kwargs['door_range']
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']

        result = _is_possible_door_open_close(grid_world, agent_id, OpenDoorActionResult, object_id, door_range)
        return result


class CloseDoorAction(Action):

    def __init__(self, duration_in_ticks=1):
        """ Action that closes doors.

        The action that closes a specific door within a given range from the agent.

        Parameters
        ----------
        duration_in_ticks : int
            The default duration of CloseDoorAction in ticks during which the GridWorld blocks the Agent performing
            other actions. By default this is 1, meaning that the OpenDoorAction will take both the tick in which it was
            decided upon and the subsequent tick. Should be zero or larger.

        """
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, **kwargs):
        """ Closes a door in the world.

        Mutates a Door object's door_status in the GridWorld to be closed (and as such not passable). It does so only if
        the Door object id exists (given as the object_id parameter) and the Door is within range (which is 1 by
        default, or overridden by a door_range parameter).

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the door is sought according to the object_id parameter.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string
            The string representing the unique identifier of the door that should be opened.
        door_range : int (default=np.inf)
            The maximum allowed distance between the agent and the door for the agent to be able to open that door.

        Returns
        -------
        CloseDoorActionResult
            The ActionResult determining the expected result of an CloseDoorAction with the given parameters.
            Can return the following results:
            The ActionResult depicting the action's success or failure and reason for that result.
            OpenDoorActionResult.NO_OBJECT_SPECIFIED    : When no object_id was given.
            OpenDoorActionResult.RESULT_SUCCESS         : When the door is opened.
        """

        # fetch options
        door_range = 1 if 'door_range' not in kwargs else kwargs['door_range']
        # object_id is required
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        if object_id is None:
            result = CloseDoorActionResult(CloseDoorActionResult.NO_OBJECT_SPECIFIED, False)
            return result

        # get obj
        obj = grid_world.environment_objects[object_id]

        # call the close door action in the object
        obj.close_door()

        result = CloseDoorActionResult(CloseDoorActionResult.RESULT_SUCCESS, True)
        return result

    def is_possible(self, grid_world, agent_id, **kwargs):
        """Check if the OpenDoorAction is possible.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the door is sought according to the object_id parameter.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string
            The string representing the unique identifier of the door that should be opened.
        door_range : int (default=np.inf)
            The maximum allowed distance between the agent and the door for the agent to be able to open that door.

        Returns
        -------
        OpenDoorActionResult
            The ActionResult determining the expected result of an CloseDoorAction with the given parameters.
            Returns the following results:
            CloseDoorActionResult.NO_DOORS_IN_RANGE      : When no EnvObject of type Door are in range.
            CloseDoorActionResult.NOT_A_DOOR             : When the given object_id does not exist.
            CloseDoorActionResult.NOT_A_DOOR             : When the given object_id does not exist.
            CloseDoorActionResult.NOT_IN_RANGE           : When the given object_id it not within range.
            CloseDoorActionResult.DOOR_ALREADY_CLOSED    : When the Door object is already closed.
            CloseDoorActionResult.DOOR_BLOCKED           : When there is another object at the Door's location.
            CloseDoorActionResult.SUCCESS                : When the door can be successfully opened.

        """
        # fetch options
        door_range = np.inf if 'door_range' not in kwargs else kwargs['door_range']
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']

        result = _is_possible_door_open_close(grid_world, agent_id, CloseDoorActionResult, object_id, door_range)
        return result


class CloseDoorActionResult(ActionResult):
    RESULT_SUCCESS = "Door was succesfully closed."
    NO_DOORS_IN_RANGE = "No door found in range"
    NOT_IN_RANGE = "Specified door is not within range."
    NOT_A_DOOR = "CloseDoor action could not be performed, as object isn't a door"
    RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'
    DOOR_ALREADY_CLOSED = "Can't close door, door is already closed."
    DOOR_BLOCKED = "Can't close door, object or agent is blocking the door opening."
    NO_OBJECT_SPECIFIED = "No object_id of a door specified to close."

    def __init__(self, result, succeeded):
        """ ActionResult for the CloseDoorAction

        The results uniquely for CloseDoorAction are (as class constants):
        CloseDoorActionResult.RESULT_SUCCESS         : When the CloseDoorAction is a success.
        CloseDoorActionResult.NO_DOORS_IN_RANGE      : When no Door objects are within the specified range.
        CloseDoorActionResult.NOT_IN_RANGE           : When the given object_id is not within the specified range.
        CloseDoorActionResult.NOT_A_DOOR             : When the given object_id does not exist.
        CloseDoorActionResult.DOOR_ALREADY_CLOSED    : When the Door is already closed.
        CloseDoorActionResult.DOOR_BLOCKED           : When another object is at the Door's location.
        CloseDoorActionResult.NO_OBJECT_SPECIFIED    : When object_id is not given.

        Parameters
        ----------
        result : string
            A string representing the reason for an CloseDoorAction's (expected) success or fail.
        succeeded : boolean
            A boolean representing the (expected) success or fail of an CloseDoorAction.

        See Also
        --------
        CloseDoorAction

        """
        super().__init__(result, succeeded)


class OpenDoorActionResult(ActionResult):
    RESULT_SUCCESS = "Door was successfully opened."
    NO_DOORS_IN_RANGE = "No door found in range"
    NOT_IN_RANGE = "Specified door is not within range."
    NOT_A_DOOR = "OpenDoor action could not be performed, as object isn't a door"
    RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'
    DOOR_ALREADY_OPEN = "Can't open door, door is already open"
    DOOR_BLOCKED = "Can't close door, object or agent is blocking the door opening."
    NO_OBJECT_SPECIFIED = "No object_id of a door specified to open."

    def __init__(self, result, succeeded):
        """ ActionResult for the OpenDoorAction

        The results uniquely for OpenDoorAction are (as class constants):
        OpenDoorActionResult.RESULT_SUCCESS         : When the OpenDoorAction is a success.
        OpenDoorActionResult.NO_DOORS_IN_RANGE      : When no Door objects are within the specified range.
        OpenDoorActionResult.NOT_IN_RANGE           : When the given object_id is not within the specified range.
        OpenDoorActionResult.NOT_A_DOOR             : When the given object_id does not exist.
        OpenDoorActionResult.DOOR_ALREADY_OPEN      : When the Door is already open.
        OpenDoorActionResult.NO_OBJECT_SPECIFIED    : When object_id is not given.

        Parameters
        ----------
        result : string
            A string representing the reason for an OpenDoorAction's (expected) success or fail.
        succeeded : boolean
            A boolean representing the (expected) success or fail of an OpenDoorAction.

        See Also
        --------
        OpenDoorAction

        """
        super().__init__(result, succeeded)


def _is_possible_door_open_close(grid_world, agent_id, action_result, object_id=None, door_range=np.inf):
    """ Private MATRX method.

    Checks if a door can be opened/closed with the given OpenDoorAction / CloseDoorAction parameters respectively.

    Parameters
    ----------
    grid_world : GridWorld
        The GridWorld instance in which the door is sought according to the object_id parameter.
    agent_id : string
        The string representing the unique identified that represents the agent performing this action.
    action_result : {Type[OpenDoorActionResult], Type[CloseDoorActionResult]}
        The type of the ActionResult that should be returned. Also used to determine for which kind of Action this check
        is made (OpenDoorAction or CloseDoorAction).
    object_id : string
        The string representing the unique identifier of the door that should be opened.
    door_range : int (default=np.inf)
        The maximum allowed distance between the agent and the door for the agent to be able to open that door.

    Returns
    -------
    ActionResult : {Type[OpenDoorActionResult], Type[CloseDoorActionResult]}
        Returns either an OpenDoorActionResult or CloseDoorActionResult (depends on the parameter action_result) that
        contains whether the respective action is possible or not.

    """
    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    loc_agent = reg_ag.location  # Agent location

    # check if there is a Door object in the scenario
    objects_in_range = grid_world.get_objects_in_range(loc_agent, object_type=Door, sense_range=door_range)

    # there is no Door in range, so not possible to open any door
    if len(objects_in_range) is 0:
        return action_result(action_result.NO_DOORS_IN_RANGE, False)

    # if we did not get a specific door to open, we simply return success as it is possible to open an arbitrary door
    # as there is atleast one door in range.
    if object_id is None:
        return action_result(action_result.RESULT_SUCCESS, True)

    # check if the given object_id even exists
    if object_id not in grid_world.environment_objects.keys():
        return action_result(action_result.NOT_A_DOOR, False)

    # check if the given object_id is an actual door in range
    if object_id not in objects_in_range.keys():
        return action_result(action_result.NOT_IN_RANGE, False)

    # get the target object
    obj = grid_world.environment_objects[object_id]

    # check if door is already open or closed
    if action_result == OpenDoorActionResult and obj.properties["is_open"]:
        return action_result(action_result.DOOR_ALREADY_OPEN, False)
    elif action_result == CloseDoorActionResult and not obj.properties["is_open"]:
        return action_result(action_result.DOOR_ALREADY_CLOSED, False)

    # when closing, check that there are no objects in the door opening
    if action_result == CloseDoorActionResult:
        # get all objects at the location of the door
        objects_in_door_opening = grid_world.get_objects_in_range(obj.location, object_type="*", sense_range=0)

        # more than 1 object at that location (besides the door itself) means the door is blocked
        if len(objects_in_door_opening) > 1:
            return action_result(action_result.DOOR_BLOCKED, False)

    return action_result(action_result.RESULT_SUCCESS, True)
