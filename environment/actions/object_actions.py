from environment.actions.action import Action, ActionResult
from environment.objects.agent_avatar import AgentAvatar
import numpy as np


class RemoveObject(Action):
    """
    An action that allows agent to remove EnvObjects (basically ALL objects) from the GridWorld permanently. This
    includes other AgentAvatars.
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
                    return True, ObjectActionResult.OBJECT_REMOVED \
                        .replace('object_id'.upper(), str(object_id))
                else:  # else we return a failure due to the GridWorld removal failed
                    return False, ObjectActionResult.REMOVAL_FAILED \
                        .replace('object_id'.upper(), str(object_id))

        # If the object was not in range, or no objects were in range we return that the object id was not in range
        return False, ObjectActionResult.OBJECT_ID_NOT_WITHIN_RANGE \
            .replace('remove_range'.upper(), str(remove_range)) \
            .replace('object_id'.upper(), str(object_id))

    def is_possible(self, grid_world, agent_id):
        agent_avatar = grid_world.get_env_object(agent_id, obj_type=AgentAvatar)  # get ourselves
        assert agent_avatar is not None  # check if we actually exist
        agent_loc = agent_avatar.location  # get our location

        remove_range = np.inf  # we do not know the intended range, so assume infinite
        # get all objects within infinite range
        objects_in_range = grid_world.get_objects_in_range(agent_loc, object_type="*", sense_range=remove_range)

        # You can't remove yourself
        objects_in_range.pop(agent_avatar.obj_id)

        if len(objects_in_range) == 0:  # if there are no objects in infinite range besides ourselves, we return fail
            return False, ObjectActionResult.NO_OBJECTS_IN_RANGE \
                .replace('remove_range'.upper(), str(remove_range))

        # otherwise some instance of RemoveObject is possible, although we do not know yet IF the intended removal is
        # possible.
        return True, None


class ObjectActionResult(ActionResult):
    NO_OBJECTS_IN_RANGE = "No objects were in `REMOVE_RANGE`."
    OBJECT_ID_NOT_WITHIN_RANGE = "The object with id `OBJECT_ID` is not within the range of `REMOVE_RANGE`."
    OBJECT_REMOVED = "The object with id `OBJECT_ID` is removed."
    REMOVAL_FAILED = "The object with id `OBJECT_ID` failed to be removed by the environment for some reason."

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)
