import numpy as np
import collections, math

from environment.actions.action import Action, ActionResult
from environment.objects.agent_avatar import AgentAvatar
from environment.objects.simple_objects import AreaTile
import copy


class RemoveObject(Action):
    """
    An action that allows agent to remove EnvObjects (basically ALL objects except YOURSELF) from the GridWorld
    permanently. This includes other AgentAvatars.
    """

    def __init__(self):
        name = RemoveObject.__name__
        super().__init__(name)

    def mutate(self, grid_world, agent_id, **kwargs):
        """
        Removes the object specified in kwargs['object_id'] permanently from the grid world if within range of
        kwargs['remove_range'] (if key exists, otherwise default range is 1).

        It does not allow you to remove itself!

        :param grid_world: The current GridWorld
        :param agent_id: The agent that performs the action.
        :param kwargs: Requires an 'object_id' that exists in the GridWorld and the optional 'remove_range' to specify
        the range in which the object can be removed. If a range is not given, defaults to 1.
        :return: An ObjectActionResult.
        """
        assert 'object_id' in kwargs.keys()  # assert if object_id is given.
        object_id = kwargs['object_id']  # assign
        remove_range = 1  # default remove range
        if 'remove_range' in kwargs.keys():  # if remove range is present
            assert isinstance(kwargs['remove_range'], int)  # should be of integer
            assert kwargs['remove_range'] >= 0  # should be equal or larger than 0
            remove_range = kwargs['remove_range']  # assign

        # get the current agent (exists, otherwise the is_possible failed)
        agent_avatar = grid_world.registered_agents[agent_id]
        agent_loc = agent_avatar.location  # current location

        # Get all objects in the remove_range
        objects_in_range = grid_world.get_objects_in_range(agent_loc, object_type="*", sense_range=remove_range)

        # You can't remove yourself
        objects_in_range.pop(agent_id)

        for obj in objects_in_range:  # loop through all objects in range
            if obj == object_id:  # if object is in that list
                success = grid_world.remove_from_grid(object_id)  # remove it, success is whether GridWorld succeeded
                if success:  # if we succeeded in removal return the appriopriate ActionResult
                    return ObjectActionResult(ObjectActionResult.OBJECT_REMOVED \
                                              .replace('object_id'.upper(), str(object_id)), True)
                else:  # else we return a failure due to the GridWorld removal failed
                    return ObjectActionResult(ObjectActionResult.REMOVAL_FAILED \
                                              .replace('object_id'.upper(), str(object_id)), False)

        # If the object was not in range, or no objects were in range we return that the object id was not in range
        return ObjectActionResult(ObjectActionResult.OBJECT_ID_NOT_WITHIN_RANGE \
                                  .replace('remove_range'.upper(), str(remove_range)) \
                                  .replace('object_id'.upper(), str(object_id)), False)

    def is_possible(self, grid_world, agent_id, **kwargs):
        agent_avatar = grid_world.get_env_object(agent_id, obj_type=AgentAvatar)  # get ourselves
        assert agent_avatar is not None  # check if we actually exist
        agent_loc = agent_avatar.location  # get our location

        remove_range = np.inf  # we do not know the intended range, so assume infinite
        # get all objects within infinite range
        objects_in_range = grid_world.get_objects_in_range(agent_loc, object_type="*", sense_range=remove_range)

        # You can't remove yourself
        objects_in_range.pop(agent_avatar.obj_id)

        if len(objects_in_range) == 0:  # if there are no objects in infinite range besides ourselves, we return fail
            return False, ObjectActionResult(ObjectActionResult.NO_OBJECTS_IN_RANGE \
                                             .replace('remove_range'.upper(), str(remove_range)), False)

        # otherwise some instance of RemoveObject is possible, although we do not know yet IF the intended removal is
        # possible.
        return True, ObjectActionResult(ObjectActionResult.ACTION_SUCCEEDED, True)


class ObjectActionResult(ActionResult):
    NO_OBJECTS_IN_RANGE = "No objects were in `REMOVE_RANGE`."
    OBJECT_ID_NOT_WITHIN_RANGE = "The object with id `OBJECT_ID` is not within the range of `REMOVE_RANGE`."
    OBJECT_REMOVED = "The object with id `OBJECT_ID` is removed."
    REMOVAL_FAILED = "The object with id `OBJECT_ID` failed to be removed by the environment for some reason."

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)


class GrabAction(Action):
    """
    An action that allows agent to grab EnvObjects (only objects) from the GridWorld. This
    excludes other AgentAvatars. Grabbing automatically is followed by carrying of the object.
    Carrying is implemented in movement actions.
    """

    def __init__(self, name=None):
        if name is None:
            name = GrabAction.__name__
        super().__init__(name)

    def is_possible(self, grid_world, agent_id, **kwargs):
        """
        This function checks if grabbing an object is possible.
        For this it assumes a infinite grab range and a random object in that range
        The check if an object is within range is done within 'mutate'
        :param grid_world: The current GridWorld
        :param agent_id: The agent that performes the action
        :return:
        """
        # Set default values check
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        grab_range = np.inf if 'grab_range' not in kwargs else kwargs['grab_range']
        max_objects = np.inf if 'max_objects' not in kwargs else kwargs['max_objects']

        return is_possible_grab(grid_world, agent_id=agent_id, object_id=object_id, grab_range=grab_range,
                                max_objects=max_objects)

    def mutate(self, grid_world, agent_id, **kwargs):
        """
        Picks up the object specified in kwargs['object_id']  if within range of
        kwargs['grab_range'] (if key exists, otherwise default range is 0).

        It does not allow you to grab yourself/other agents

        :param grid_world: The current GridWorld
        :param agent_id: The agent that performs the action.
        :param kwargs: An optional 'object_id' that exists in the GridWorld (if none is specified
        a random object within range is chosen).\n
        Optional 'grab_range' to specify the range in which the object can be removed.
        If a range is not given, defaults to 0. \n
        Optional 'max_objects' for the amount of objects the agent can carry.
        If no 'max_objects' is set, default is set to 1.
        :return: An ObjectActionResult.
        """

        # Additional check
        assert 'object_id' in kwargs.keys()
        assert 'grab_range' in kwargs.keys()
        assert 'max_objects' in kwargs.keys()

        # if possible:
        object_id = kwargs['object_id']  # assign

        # Loading properties
        reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
        env_obj = grid_world.environment_objects[object_id]  # Environment object

        # Updating properties
        env_obj.carried_by.append(agent_id)
        reg_ag.is_carrying.append(env_obj)  # we add the entire object!

        # Remove it from the grid world (it is now stored in the is_carrying list of the AgentAvatar
        succeeded = grid_world.remove_from_grid(object_id=env_obj.obj_id, remove_from_carrier=False)
        if not succeeded:
            return GrabActionResult(GrabActionResult.FAILED_TO_REMOVE_OBJECT_FROM_WORLD.replace("{OBJECT_ID}",
                                                                                                env_obj.obj_id), False)

        # Updating Location (done after removing from grid, or the grid will search the object on the wrong location)
        env_obj.location = reg_ag.location

        return GrabActionResult(GrabActionResult.RESULT_SUCCESS, True)


def is_possible_grab(grid_world, agent_id, object_id, grab_range, max_objects):
    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    loc_agent = reg_ag.location  # Agent location

    if object_id is None:
        return False, GrabActionResult(GrabActionResult.RESULT_NO_OBJECT, False)

    # Already carries an object
    if len(reg_ag.is_carrying) >= max_objects:
        return False, GrabActionResult(GrabActionResult.RESULT_CARRIES_OBJECT, False)

    # Go through all objects at the desired locations
    objects_in_range = grid_world.get_objects_in_range(loc_agent, object_type="*", sense_range=grab_range)
    objects_in_range.pop(agent_id)

    # Set random object in range
    if not object_id:
        # Remove all non objects from the list
        for obj in list(objects_in_range.keys()):
            if obj not in grid_world.environment_objects.keys():
                objects_in_range.pop(obj)

        # Select a random object
        if objects_in_range:
            object_id = grid_world.rnd_gen.choice(list(objects_in_range.keys()))
        else:
            return False, GrabActionResult(GrabActionResult.NOT_IN_RANGE, False)

    # Check if object is in range
    if object_id not in objects_in_range:
        return False, GrabActionResult(GrabActionResult.NOT_IN_RANGE, False)

    # Check if object_id is the id of an agent
    if object_id in grid_world.registered_agents.keys():
        # If it is an agent at that location, grabbing is not possible
        return False, GrabActionResult(GrabActionResult.RESULT_AGENT, False)

    # Check if it is an object
    if object_id in grid_world.environment_objects.keys():
        env_obj = grid_world.environment_objects[object_id]  # Environment object
        # Check if the object is not carried by another agent
        if len(env_obj.carried_by) != 0:
            return False, GrabActionResult(GrabActionResult.RESULT_OBJECT_CARRIED.replace("{AGENT_ID}",
                                                                                          str(env_obj.carried_by)),
                                           False)
        elif not env_obj.properties["is_movable"]:
            return False, GrabActionResult(GrabActionResult.RESULT_OBJECT_UNMOVABLE, False)
        else:
            # Success
            return True, GrabActionResult(GrabActionResult.RESULT_SUCCESS, False)
    else:
        return False, GrabActionResult(GrabActionResult.RESULT_UNKNOWN_OBJECT_TYPE, False)


class GrabActionResult(ActionResult):
    FAILED_TO_REMOVE_OBJECT_FROM_WORLD = 'Grab action failed; could not remove object with id {OBJECT_ID} from grid.'
    RESULT_SUCCESS = 'Grab action success'
    NOT_IN_RANGE = 'Object not in range'
    RESULT_AGENT = 'This is an agent, cannot be picked up'
    RESULT_NO_OBJECT = 'No Object specified'
    RESULT_CARRIES_OBJECT = 'Agent already carries the maximum amount of objects'
    RESULT_OBJECT_CARRIED = 'Object is already carried by {AGENT_ID}'
    RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'
    RESULT_OBJECT_UNMOVABLE = 'Object is not movable'

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)


class DropAction(Action):
    def __init__(self, name=None):
        if name is None:
            name = DropAction.__name__
        super().__init__(name)


    def is_possible(self, grid_world, agent_id, **kwargs):
        reg_ag = grid_world.registered_agents[agent_id]

        drop_range = 1 if not 'drop_range' in kwargs else kwargs['drop_range']

        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            obj_id = kwargs['object_id']
        elif len(reg_ag.is_carrying) > 0:
            obj_id = reg_ag.is_carrying[-1]
        else:
            return False, DropActionResult(DropActionResult.RESULT_NO_OBJECT, False)

        return possible_drop(grid_world, agent_id=agent_id, obj_id=obj_id, drop_range=drop_range)


    def mutate(self, grid_world, agent_id, **kwargs):
        """
        This function drops one of the items carried by the agent.
        It tries to drop the object within the specified drop_range around the agent,
        trying to drop it as close to the agent as possible

        :param grid_world: pointer to current GridWorld
        :param agent_id: agent that acts
        :param kwargs: Optional an "object_id" can be given. If an agent is carrying
        two or more items, this specifies which item should be dropped.
        :return: Always True
        """
        reg_ag = grid_world.registered_agents[agent_id]

        # fetch range from kwargs
        drop_range = 1 if not 'drop_range' in kwargs else kwargs['drop_range']

        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            env_obj = kwargs['object_id']
        elif len(reg_ag.is_carrying) > 0:
            env_obj = reg_ag.is_carrying[-1]
        else:
            return DropActionResult(DropActionResult.RESULT_NO_OBJECT_CARRIED, False)

        # check that it is even possible to drop this object somewhere
        if not env_obj.is_traversable and not reg_ag.is_traversable and drop_range == 0:
            raise Exception(
                f"Intraversable agent {reg_ag.obj_id} can only drop the intraversable object {env_obj.obj_id} at its own location (drop_range = 0), but this is impossible. Enlarge the drop_range for the DropAction to atleast 1")

        # check if we can drop it at our current location
        curr_loc_drop_poss = is_drop_poss(grid_world, env_obj, reg_ag.location)

        # drop it on the agent location if possible
        if curr_loc_drop_poss:
            return act_drop(grid_world, agent=reg_ag, env_obj=env_obj, drop_loc=reg_ag.location)

        # if the agent location was the only within range, return a negative action result
        elif not curr_loc_drop_poss and drop_range == 0:
            return DropActionResult(DropActionResult.RESULT_OBJECT, False)

        # Try finding other drop locations from close to further away around the agent
        drop_loc = find_drop_loc(grid_world, reg_ag, env_obj, drop_range, reg_ag.location)

        # If we didn't find a valid drop location within range, return a negative action result
        if not drop_loc:
            return DropActionResult(DropActionResult.RESULT_OBJECT, False)

        return act_drop(grid_world, agent=reg_ag, env_obj=env_obj, drop_loc=drop_loc)


def act_drop(grid_world, agent, env_obj, drop_loc):
    """ Drop the object """

    # Updating properties
    agent.is_carrying.remove(env_obj)
    env_obj.carried_by.remove(agent.obj_id)

    # We return the object to the grid location we are standing at
    env_obj.location = drop_loc
    grid_world.register_env_object(env_obj)

    return DropActionResult(DropActionResult.RESULT_SUCCESS, True)


def find_drop_loc(grid_world, agent, env_obj, drop_range, start_loc):
    """
    Do a breadth first search starting from the agent's location to find
    the closest valid drop location.

    :param grid_world: The grid_world object
    :param reg_ag: the agent object of the agent who wants to drop the object
    :param env_obj: the object to be dropped
    :param drop_range: the range from our current location for which we can drop
    the object
    :return: False if no valid drop location can be found, otherwise the [x,y]
    coords of the closest drop location
    """
    queue = collections.deque([[start_loc]])
    seen = set([start_loc])

    width = grid_world.shape[0]
    height = grid_world.shape[1]

    while queue:
        path = queue.popleft()
        x, y = path[-1]

        # check if we are still within drop_range
        if get_distance([x, y], start_loc) > drop_range:
            return False

        # check if we can drop at this location
        if is_drop_poss(grid_world, env_obj, [x, y]):
            return [x, y]

        # queue unseen neighbouring tiles
        for x2, y2 in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= x2 < width and 0 <= y2 < height and (x2, y2) not in seen:
                queue.append(path + [(x2, y2)])
                seen.add((x2, y2))
    return False


def get_distance(coord1, coord2):
    """ Get distance between two x,y coordinates """
    dist = [(a - b) ** 2 for a, b in zip(coord1, coord2)]
    dist = math.sqrt(sum(dist))
    return dist


def is_drop_poss(grid_world, env_obj, dropLocation):
    """
    Check if the object can be dropped at a specific location by checking if
    there are any intraversable objects at that location, and if the object to
    be dropped is intraversable
    :param grid_world: The grid_world object
    :param env_obj: the object to be dropped
    :param dropLocation: location to check if it is possible to drop the env_obj there
    """

    # Count the intraversable objects at the current location if we would drop the
    # object here
    objs_at_loc = grid_world.get_objects_in_range(dropLocation, object_type="*", sense_range=0)

    # Remove area objects from the list
    for i in range(len(objs_at_loc),0):
        if isinstance(objs_at_loc[i], AreaTile):
            del objs_at_loc[i]

    in_trav_objs_count = 1 if not env_obj.is_traversable else 0
    in_trav_objs_count += len([obj for obj in objs_at_loc if not objs_at_loc[obj].is_traversable])

    # check if we would have an in_traversable object and other objects in
    # the same location (which is impossible)
    if in_trav_objs_count >= 1 and (len(objs_at_loc) + 1) >= 2:
        return False
    else:
        return True


def possible_drop(grid_world, agent_id, obj_id, drop_range):
    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    loc_agent = reg_ag.location
    loc_obj_ids = grid_world.grid[loc_agent[1], loc_agent[0]]

    # No object given
    if not obj_id:
        return False, DropActionResult(DropActionResult.RESULT_NONE_GIVEN, False)

    # No object with that name
    if not (obj_id in reg_ag.is_carrying):
        return False, DropActionResult(DropActionResult.RESULT_NO_OBJECT, False)

    if len(loc_obj_ids) == 1:
        return True, DropActionResult(DropActionResult.RESULT_SUCCESS, True)

    # TODO: incorporate is_possible check from DropAction.mutate is_possible here

    return True, DropActionResult(DropActionResult.RESULT_SUCCESS, True)


class DropActionResult(ActionResult):
    RESULT_SUCCESS = 'Drop action success'
    RESULT_NO_OBJECT = 'The item is not carried'
    RESULT_NONE_GIVEN = "'None' used as input id"
    RESULT_AGENT = 'Cannot drop item on an agent'
    RESULT_OBJECT = 'Cannot drop item on another intraversable object'
    RESULT_UNKNOWN_OBJECT_TYPE = 'Cannot drop item on an unknown object'
    RESULT_NO_OBJECT_CARRIED = 'Cannot drop object when none carried'

    def __init__(self, result, succeeded, obj_id=None):
        super().__init__(result, succeeded)
        self.obj_id = obj_id
