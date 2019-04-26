from environment.actions.action import Action, ActionResult

class DropAction(Action):
    def __init__(self, name=None):
        if name is None:
            name = DropAction.__name__
        super().__init__(name)

    def is_possible(self, grid_world, agent_id, **kwargs):
        reg_ag = grid_world.registered_agents[agent_id]

        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            obj_id = kwargs['object_id']
        elif len(reg_ag.properties['carrying']) > 0:
            obj_id = reg_ag.properties['carrying'][-1]
        else:
            return False, DropActionResult.RESULT_NO_OBJECT

        return possible_drop(grid_world, agent_id=agent_id, obj_id=obj_id)

    def mutate(self, grid_world, agent_id, **kwargs):
        """
        This function drops one of the items carried by the agent.
        It drops the item at the current location of the agent.

        :param grid_world: pointer to current GridWorld
        :param agent_id: agent that acts
        :param kwargs: Optional an "object_id" can be given. If an agent is carrying
        two or more items, this specifies which item should be dropped.
        :return: Always True
        """
        reg_ag = grid_world.registered_agents[agent_id]

        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            obj_id = kwargs['object_id']
        elif len(reg_ag.properties['carrying']) > 0:
            obj_id = reg_ag.properties['carrying'][-1]
        else:
            return False

        return act_drop(grid_world, agent_id=agent_id, obj_id=obj_id)


def act_drop(grid_world, agent_id, obj_id):
    # Loading properties
    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    env_obj = grid_world.environment_objects[obj_id]  # Environment object

    # Updating properties
    reg_ag.properties['carrying'].remove(obj_id)
    env_obj.carried_by_agent_id = None
    return True


def possible_drop(grid_world, agent_id, obj_id):
    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    loc_agent = reg_ag.location
    loc_obj_ids = grid_world.grid[loc_agent[1], loc_agent[0]]

    # No object given
    if not obj_id:
        return False, DropActionResult.RESULT_NONE_GIVEN

    # No object with that name
    if not (obj_id in reg_ag.properties['carrying']):
        return False, DropActionResult.RESULT_NO_OBJECT

    # No other object/agent is in that location, then drop is a success
    if len(loc_obj_ids) == len(reg_ag.properties['carrying']) + 1:
        return True, DropActionResult.RESULT_SUCCESS

    # Go through all objects at the desired locations
    for loc_obj_id in loc_obj_ids:
        # Check if loc_obj_id is the id of an agent
        if loc_obj_id in grid_world.registered_agents.keys():
            # If it is an agent at that location, dropping is not possible
            return False, DropActionResult.RESULT_AGENT

        # Check if it is an object
        if loc_obj_id in grid_world.environment_objects.keys():
            return False, DropActionResult.RESULT_OBJECT
        else:
            # We have checked for agent and object, unknown what to do
            return False, DropActionResult.RESULT_UNKNOWN_OBJECT_TYPE


class DropActionResult(ActionResult):
    RESULT_SUCCESS = 'Drop action success'
    RESULT_NO_OBJECT = 'The item is not carried'
    RESULT_NONE_GIVEN = "'None' used as input id"
    RESULT_AGENT = 'Cannot drop item on an agent'
    RESULT_OBJECT = 'Cannot drop item on another object'
    RESULT_UNKNOWN_OBJECT_TYPE = 'Cannot drop item on an unknown object'

    def __init__(self, result, succeeded, obj_id=None):
        super().__init__(result, succeeded)
        self.obj_id = obj_id