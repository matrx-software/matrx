from environment.actions.action import Action, ActionResult

def act_grab(grid_world, agent_id):
    result = possible_grab(grid_world, agent_id) 
    if result.succeeded:
        loc_agent = grid_world.registered_agents[agent_id].location
        grid_world.environment_objects[result.obj_id].location[0] = 0
        grid_world.environment_objects[result.obj_id].location[1] = 0
        print("Grabed")
    return result

def is_possible_grab(grid_world, agent_id):
    result = possible_grab(grid_world, agent_id)
    return result.succeeded

def possible_grab(grid_world, agent_id):
    loc_agent = grid_world.registered_agents[agent_id].location        
    loc_obj_ids = grid_world.grid[loc_agent[1], loc_agent[0]]

    if loc_obj_ids is None:
        return GrabActionResult(GrabActionResult.RESULT_NO_OBJECT, succeeded=False)
    else:
         # Go through all objects at the desired locations
        for loc_obj_id in loc_obj_ids:
            # Check if loc_obj_id is the id of an agent
            if loc_obj_id in grid_world.registered_agents.keys():
                # If it is an agent grabing is not possible
                return GrabActionResult(GrabActionResult.RESULT_AGENT, succeeded=False)
            else:
                return GrabActionResult(GrabActionResult.RESULT_SUCCESS, succeeded=True, obj_id = loc_obj_id)
                

class GrabActionResult(ActionResult):
    RESULT_SUCCESS = 'Grab action success'
    RESULT_AGENT = 'This is an agent, cannot be picked up'
    RESULT_NO_OBJECT = 'There is nothing in this location'    
    
    def __init__(self, result, succeeded, obj_id = None):
        super().__init__(result, succeeded)
        self.obj_id = obj_id

class GrabAction(Action):

    def __init__(self, name=None):
        if name is None:
            name = GrabAction.__name__
        super().__init__(name)

    def is_possible(self, grid_world, agent_id, **kwargs):        
        return is_possible_grab(grid_world, agent_id=agent_id)

    def mutate(self, grid_world, agent_id, **kwargs):
        return act_grab(grid_world, agent_id=agent_id)