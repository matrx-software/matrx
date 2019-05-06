from environment.actions.action import Action, ActionResult
import numpy as np

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
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        grab_range = 0 if 'grab_range' not in kwargs else kwargs['grab_range']
        max_objects = 1 if 'max_objects' not in kwargs else kwargs['max_objects']

        # if possible:
        object_id = kwargs['object_id']  # assign

        # Loading properties
        reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
        env_obj = grid_world.environment_objects[object_id]  # Environment object

        # Updating properties
        reg_ag.properties['carrying'].append(object_id)
        env_obj.properties['carried'].append(agent_id)

        # Updating Location
        env_obj.location = reg_ag.location

        return GrabActionResult(GrabActionResult.RESULT_SUCCESS, True)



def is_possible_grab(grid_world, agent_id, object_id, grab_range, max_objects):
    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    loc_agent = reg_ag.location  # Agent location

    # Already carries an object
    if len(reg_ag.properties['carrying']) >= max_objects:
        return False, GrabActionResult.RESULT_CARRIES_OBJECT

    # Go through all objects at the desired locations
    objects_in_range = grid_world.get_objects_in_range(loc_agent, object_type="*", sense_range=grab_range)
    objects_in_range.pop(agent_id)

    # Removing carried objects
    for obj in reg_ag.properties['carrying']:
        objects_in_range.pop(obj)

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
            return False, GrabActionResult.NOT_IN_RANGE

    # Check if object is in range
    if object_id not in objects_in_range:
        return False, GrabActionResult.NOT_IN_RANGE

    # Check if object_id is the id of an agent
    if object_id in grid_world.registered_agents.keys():
        # If it is an agent at that location, grabbing is not possible
        return False, GrabActionResult.RESULT_AGENT

    # Check if it is an object
    if object_id in grid_world.environment_objects.keys():
        env_obj = grid_world.environment_objects[object_id]  # Environment object
        # Check if the object is not carried by another agent
        if env_obj.properties['carried']:
            return False, GrabActionResult.RESULT_OBJECT_CARRIED
        elif not env_obj.properties["movable"]:
            return False, GrabActionResult.RESULT_OBJECT_UNMOVABLE
        else:
            # Success
            return True, GrabActionResult.RESULT_SUCCESS
    else:
        return False, GrabActionResult.RESULT_UNKNOWN_OBJECT_TYPE


class GrabActionResult(ActionResult):
    RESULT_SUCCESS = 'Grab action success'
    NOT_IN_RANGE = 'Object not in range'
    RESULT_AGENT = 'This is an agent, cannot be picked up'
    RESULT_NO_OBJECT = 'No Object specified'
    RESULT_CARRIES_OBJECT = 'Agent already carries the maximum amount of objects'
    RESULT_OBJECT_CARRIED = 'Object is already carried'
    RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'
    RESULT_OBJECT_UNMOVABLE = 'Object is not movable'

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)
