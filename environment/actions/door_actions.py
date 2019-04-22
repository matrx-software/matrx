import numpy as np

from environment.actions.action import Action, ActionResult
from environment.objects.basic_objects import Door

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
        door_range = 0 if 'door_range' not in kwargs else kwargs['door_range']
        # object_id is required
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        if object_id == None:
            return False, OpenDoorActionResult.NO_OBJECT_SPECIFIED

        # get obj
        obj = grid_world.environment_objects[object_id]

        # set door to open, traversable, and change colour
        obj.properties["door_open"] = True
        obj.properties["colour"] = "#9c9c9c"
        obj.is_traversable = True

        return True, OpenDoorActionResult.OPEN_RESULT_SUCCESS


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

        return is_possible_door_open_close(grid_world, agent_id, "open", object_id, door_range)




class OpenDoorActionResult(ActionResult):

    OPEN_RESULT_SUCCESS = "Door was succesfully opened."
    ACTION_NOT_POSSIBLE = "The `is_possible(...)` method return False. Signalling that the action was not possible."
    UNKNOWN_ACTION = "The action is not known to the environment."
    NO_DOORS_IN_RANGE = "No door found in range"
    NOT_IN_RANGE = "Specified door is not within range."
    NO_ACTION_GIVEN = "There was no action given to perform, automatic succeed."
    NOT_A_DOOR = "Opendoor action could not be performed, as object isn't a door"
    RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'
    DOOR_ALREADY_OPEN = "Can't open door, door is already open"
    NO_OBJECT_SPECIFIED = "No object_id of a door specified to open."

    def __init__(self, result, succeeded):
        self.result = result
        self.succeeded = succeeded



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
            return False, CloseDoorActionResult.NO_OBJECT_SPECIFIED

        # get obj
        obj = grid_world.environment_objects[object_id]

        # set door to closed, intraversable, and change colour
        obj.properties["door_open"] = False
        obj.properties["colour"] = "#5a5a5a"
        obj.is_traversable = False

        return True, CloseDoorActionResult.CLOSE_RESULT_SUCCESS


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

        return is_possible_door_open_close(grid_world, agent_id, "close", object_id, door_range)



class CloseDoorActionResult(OpenDoorActionResult):

    CLOSE_RESULT_SUCCESS = "Door was succesfully closed."
    NOT_A_DOOR = "Closedoor action could not be performed, as object isn't a door"
    RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'
    DOOR_ALREADY_CLOSED = "Can't close door, door is already closed."
    DOOR_BLOCKED = "Can't close door, object or agent is blocking the door opening."
    NO_OBJECT_SPECIFIED = "No object_id of a door specified to close."

    def __init__(self, result, succeeded):
        self.result = result
        self.succeeded = succeeded



def is_possible_door_open_close(grid_world, agent_id, open_close, object_id=None, door_range=np.inf):
    """
    Same as is_possible, but this function uses the action_kwargs to get a more accurate prediction.
    Can be used both for checking if the door is already open or closed
    """
    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    loc_agent = reg_ag.location  # Agent location

    # check if there is a Door object in the scenario
    objects_in_range = grid_world.get_objects_in_range(loc_agent, object_type=Door, sense_range=door_range)

    # We don't get a specific target door passed, so check if the action would
    # be possible in principle
    if object_id == None:
        # there is no Door in this complete scenario, so not possible
        if len(objects_in_range) is 0:
            return False, OpenDoorActionResult.NO_DOORS_IN_RANGE
        # There is a door present, so it might be possible to perform this action
        else:
            return True, None

    # check if it is an object
    if not object_id in grid_world.environment_objects.keys():
        return False, OpenDoorActionResult.NOT_A_DOOR

    # get the target object
    obj = grid_world.environment_objects[object_id]

    # check if the object is a door or not
    if not ("type" in obj.properties and obj.properties["type"] == "Door"):
        return False, OpenDoorActionResult.NOT_A_DOOR

    # Check if object is in range
    if object_id not in objects_in_range:
        return False, OpenDoorActionResult.NOT_IN_RANGE

    # check if door is already open or closed
    if open_close == "open" and obj.properties["door_open"]:
        return False, OpenDoorActionResult.DOOR_ALREADY_OPEN
    elif open_close == "close" and not obj.properties["door_open"]:
        return False, CloseDoorActionResult.DOOR_ALREADY_CLOSED

    # when closing, check that there are no objects in the door opening
    if open_close == "close":
        # get all objects at the location of the door
        objects_in_dooropening = grid_world.get_objects_in_range(obj.location, object_type="*", sense_range=0)

        # more than 1 object at that location (the door itself) means the door is blocked
        if len(objects_in_dooropening) > 1:
            return False, CloseDoorActionResult.DOOR_BLOCKED

    return True, None
