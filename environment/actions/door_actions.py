import numpy as np

from environment.actions.action import Action, ActionResult
from environment.objects.simple_objects import Door


class OpenDoorAction(Action):
    """
    Action to open a Door
    """

    def __init__(self, name=None, duration_in_ticks=1):
        """
        :param name: The name of the action.
        :param duration_in_ticks: The duration of the action in ticks. By default this is 1.
        """
        if name is None:
            name = OpenDoorAction.__name__
        super().__init__(name, 3)

    def mutate(self, grid_world, agent_id, **kwargs):
        """
        Performs the actual action in the world.
        Opens the door, by changing the colour and setting the open_door property

        :param grid_world: A pointer to the actual world object.
        :param agent_id: The id known in the grid world as an agent that peforms this action.
        :param kwargs: Requires the door_range (int indicating cells range) and object_id arguments.
        :return: An action result depicting the action's success or failure and reason/description of that result.
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
        """
        Checks whether the action is possible in the world when performed by the given agent.

        :param grid_world: A pointer to the actual world object.
        :param agent_id: The id known in the grid world as an agent that peforms this action.
        :return: Returns two things; a boolean signalling whether the action is possible or not, and a string telling
        you why the action was not possible.
        """
        # fetch options
        door_range = np.inf if 'door_range' not in kwargs else kwargs['door_range']
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']

        result = is_possible_door_open_close(grid_world, agent_id, OpenDoorActionResult, object_id, door_range)
        return result.succeeded, result.result


class CloseDoorAction(Action):
    """
    Action to open a Door
    """

    def __init__(self, name=None, duration_in_ticks=1):
        """
        :param name: The name of the action.
        :param duration_in_ticks: The duration of the action in ticks. By default this is 1.
        """
        if name is None:
            name = CloseDoorAction.__name__
        super().__init__(name, 3)

    def mutate(self, grid_world, agent_id, **kwargs):
        """
        Performs the actual action in the world.
        Opens the door, by changing the colour and setting the open_door property

        :param grid_world: A pointer to the actual world object.
        :param agent_id: The id known in the grid world as an agent that peforms this action.
        :param kwargs: Requires the door_range (int indicating cells range) and object_id arguments.
        :return: An action result depicting the action's success or failure and reason/description of that result.
        """

        # fetch options
        door_range = 1 if 'door_range' not in kwargs else kwargs['door_range']
        # object_id is required
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        if object_id == None:
            result = CloseDoorActionResult(CloseDoorActionResult.NO_OBJECT_SPECIFIED, False)
            return result

        # get obj
        obj = grid_world.environment_objects[object_id]

        # call the close door action in the object
        obj.close_door()

        result = CloseDoorActionResult(CloseDoorActionResult.RESULT_SUCCESS, True)
        return result

    def is_possible(self, grid_world, agent_id, **kwargs):
        """
        Checks whether the action is possible in the world when performed by the given agent.

        :param grid_world: A pointer to the actual world object.
        :param agent_id: The id known in the grid world as an agent that peforms this action.
        :return: Returns two things; a boolean signalling whether the action is possible or not, and a string telling
        you why the action was not possible.
        """
        # fetch options
        door_range = np.inf if 'door_range' not in kwargs else kwargs['door_range']
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']

        result = is_possible_door_open_close(grid_world, agent_id, CloseDoorActionResult, object_id, door_range)
        return result.succeeded, result.result


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
        super().__init__(result, succeeded)


def is_possible_door_open_close(grid_world, agent_id, action_result, object_id=None, door_range=np.inf):
    """
    Same as is_possible, but this function uses the action_kwargs to get a more accurate prediction.
    Can be used both for checking if the door is already open or closed
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
