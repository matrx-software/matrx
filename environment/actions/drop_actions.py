from environment.actions.action import Action, ActionResult


def act_drop(grid_world, agent_id, obj_id):
    # Checking if drop is possible
    result = possible_drop(grid_world, agent_id, obj_id)

    # Loading properties
    reg_ag = grid_world.registered_agents[agent_id] #Registered Agent
    env_obj = grid_world.environment_objects[obj_id] #Environment object

    # Updating properties
    reg_ag.properties['carrying'].remove(obj_id)
    env_obj.properties['carried'].remove(agent_id)
    return True


def is_possible_drop(grid_world, agent_id, obj_id):
    result = possible_drop(grid_world, agent_id, obj_id)
    return result.succeeded, result.result


def possible_drop(grid_world, agent_id, obj_id):
    reg_ag = grid_world.registered_agents[agent_id] #Registered Agent
    loc_agent = reg_ag.location        
    loc_obj_ids = grid_world.grid[loc_agent[1], loc_agent[0]]

    # No object given
    if not obj_id:
        return DropActionResult(DropActionResult.RESULT_NONE_GIVEN, succeeded=False)

    # No object with that name
    if not (obj_id in reg_ag.properties['carrying']):
        return DropActionResult(DropActionResult.RESULT_NO_OBJECT, succeeded=False)

    # No other object/agent is in that location, then drop is a success
    if len(loc_obj_ids) == 2:
        return DropActionResult(DropActionResult.RESULT_SUCCESS, succeeded=True)

    # Go through all objects at the desired locations
    for loc_obj_id in loc_obj_ids:
        # Check if loc_obj_id is the id of an agent
        if loc_obj_id in grid_world.registered_agents.keys():
            # If it is an agent at that location, dropping is not possible
            return DropActionResult(DropActionResult.RESULT_AGENT, succeeded=False)
        
        # Check if it is an object
        if loc_obj_id in grid_world.environment_objects.keys():
            return DropActionResult(DropActionResult.RESULT_OBJECT, succeeded=False)
        else:
            return DropActionResult(DropActionResult.RESULT_UNKNOWN_OBJECT_TYPE, succeeded=False)
        

class DropActionResult(ActionResult):
    RESULT_SUCCESS = 'Drop action success'
    RESULT_NO_OBJECT = 'The item is not carried'
    RESULT_NONE_GIVEN = "'None' used as input id"
    RESULT_AGENT = 'Cannot drop item on an agent'
    RESULT_OBJECT = 'Cannot drop item on another object'
    RESULT_UNKNOWN_OBJECT_TYPE = 'Cannot drop item on an unknown object'

    def __init__(self, result, succeeded, obj_id = None):
        super().__init__(result, succeeded)
        self.obj_id = obj_id


class DropAction(Action):
    def __init__(self, name=None):
        if name is None:
            name = DropAction.__name__
        super().__init__(name)

    def is_possible(self, grid_world, agent_id, obj_id=None, **kwargs):
        reg_ag = grid_world.registered_agents[agent_id]

        # If no object id is given, the last item is dropped
        if not obj_id and len(reg_ag.properties['carrying']) > 0:
            obj_id = reg_ag.properties['carrying'][-1]

        return is_possible_drop(grid_world, agent_id=agent_id, obj_id=obj_id)

    def mutate(self, grid_world, agent_id, obj_id=None, **kwargs):
        reg_ag = grid_world.registered_agents[agent_id]

        # If no object id is given, the last item is dropped
        if not obj_id and len(reg_ag.properties['carrying']) > 0:
            obj_id = reg_ag.properties['carrying'][-1]

        return act_drop(grid_world, agent_id=agent_id, obj_id=obj_id)