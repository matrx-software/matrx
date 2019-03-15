from environment.actions.action import Action, ActionResult


def act_move(grid_world, agent_id, dx, dy):
    result = possible_movement(grid_world, agent_id, dx, dy)
    if result.succeeded:
        loc = grid_world.registered_agents[agent_id].location
        new_loc = (loc[0] + dx, loc[1] + dy)
        grid_world.registered_agents[agent_id].location = new_loc
    return result


def is_possible_movement(grid_world, agent_id, dx, dy):
    result = possible_movement(grid_world, agent_id, dx, dy)
    return result.succeeded


def possible_movement(grid_world, agent_id, dx, dy):
    loc = grid_world.registered_agents[agent_id].location
    new_loc = (loc[0] + dx, loc[1] + dy)
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
                    # Check if the agent that takes the move action is not that agent and agents cannot be at the same
                    # spot, if this is the case then is_passable is False.
                    if not grid_world.can_occupy_agent_locs and loc_obj_id != agent_id:
                        # The desired location contains a different agent and we cannot step at locations with agents
                        return MoveActionResult(MoveActionResult.RESULT_OCCUPIED, succeeded=False)
                # If there are no agents at the desired location or we can move on top of other agents, we check if
                # there are objects in the way that are not passable.
                if loc_obj_id in grid_world.environment_objects.keys():
                    # get the actual object
                    loc_obj = grid_world.environment_objects[loc_obj_id]
                    # Check if the object is not passable, if this is not the case is_passable is False
                    if not loc_obj.is_passable:
                        # The desired location contains an object that is not passable
                        return MoveActionResult(MoveActionResult.RESULT_NOT_PASSABLE_OBJECT, succeeded=False)

        # Either the desired location contains the agent at previous tick, and/or all objects there are passable
        return MoveActionResult(MoveActionResult.RESULT_SUCCESS, succeeded=True)
    else:
        return MoveActionResult(MoveActionResult.RESULT_OUT_OF_BOUNDS, succeeded=False)


class MoveActionResult(ActionResult):
    RESULT_SUCCESS = 'Move action success'
    RESULT_OUT_OF_BOUNDS = 'Move action out of bounds'
    RESULT_OCCUPIED = 'Move action towards occupied space'
    RESULT_NOT_PASSABLE_OBJECT = 'Move action toward space which is not movable by agent due object'

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)


class MoveNorth(Action):

    def __init__(self, name=None):
        if name is None:
            name = MoveNorth.__name__
        super().__init__(name)
        self.dx = 0
        self.dy = -1

    def is_possible(self, grid_world, agent_id, **kwargs):
        return is_possible_movement(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)

    def mutate(self, grid_world, agent_id, **kwargs):
        return act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)


class MoveNorthEast(Action):

    def __init__(self, name=None):
        if name is None:
            name = MoveNorthEast.__name__
        super().__init__(name)
        self.dx = +1
        self.dy = -1

    def is_possible(self, grid_world, agent_id, **kwargs):
        return is_possible_movement(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)

    def mutate(self, grid_world, agent_id, **kwargs):
        return act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)


class MoveEast(Action):

    def __init__(self, name=None):
        if name is None:
            name = MoveEast.__name__
        super().__init__(name)
        self.dx = +1
        self.dy = 0

    def is_possible(self, grid_world, agent_id, **kwargs):
        return is_possible_movement(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)

    def mutate(self, grid_world, agent_id, **kwargs):
        return act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)


class MoveSouthEast(Action):

    def __init__(self, name=None):
        if name is None:
            name = MoveSouthEast.__name__
        super().__init__(name)
        self.dx = +1
        self.dy = +1

    def is_possible(self, grid_world, agent_id, **kwargs):
        return is_possible_movement(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)

    def mutate(self, grid_world, agent_id, **kwargs):
        return act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)


class MoveSouth(Action):

    def __init__(self, name=None):
        if name is None:
            name = MoveSouth.__name__
        super().__init__(name)
        self.dx = 0
        self.dy = +1

    def is_possible(self, grid_world, agent_id, **kwargs):
        return is_possible_movement(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)

    def mutate(self, grid_world, agent_id, **kwargs):
        return act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)


class MoveSouthWest(Action):

    def __init__(self, name=None):
        if name is None:
            name = MoveSouthWest.__name__
        super().__init__(name)
        self.dx = -1
        self.dy = +1

    def is_possible(self, grid_world, agent_id, **kwargs):
        return is_possible_movement(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)

    def mutate(self, grid_world, agent_id, **kwargs):
        return act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)


class MoveWest(Action):

    def __init__(self, name=None):
        if name is None:
            name = MoveWest.__name__
        super().__init__(name)
        self.dx = -1
        self.dy = 0

    def is_possible(self, grid_world, agent_id, **kwargs):
        return is_possible_movement(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)

    def mutate(self, grid_world, agent_id, **kwargs):
        return act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)


class MoveNorthWest(Action):

    def __init__(self, name=None):
        if name is None:
            name = MoveNorthWest.__name__
        super().__init__(name)
        self.dx = -1
        self.dy = -1

    def is_possible(self, grid_world, agent_id, **kwargs):
        return is_possible_movement(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)

    def mutate(self, grid_world, agent_id, **kwargs):
        return act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)
