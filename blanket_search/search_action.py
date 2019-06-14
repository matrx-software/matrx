from environment.actions.action import Action, ActionResult


def search(grid_world, agent_id):
    print("TODO: implement search method")


def is_possible_search(grid_world, agent_id):
    return True

class SearchResult(ActionResult):
    RESULT_SUCCESS = 'Search action success'

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)

class Search(Action):
    def __init__(self, name=None):
        super().__init__(name)