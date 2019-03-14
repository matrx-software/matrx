

class Action:

    def __init__(self, name):
        self.name = name

    def mutate(self, grid_world, agent_id):
        pass

    def is_possible(self, grid_world, agent_id):
        pass


class ActionResult:

    UNKNOWN_ACTION = "The action is not known to the environment."
    NO_ACTION_GIVEN = "There was no action given to perform, automatic succeed."

    def __init__(self, result, succeeded):
        self.result = result
        self.succeeded = succeeded
