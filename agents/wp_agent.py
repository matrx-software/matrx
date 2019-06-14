from agents.agent import Agent
from agents.waypointnavigator import WaypointNavigator


class WPAgent(Agent):

    def __init__(self, grid_size):
        super().__init__()
        self.wp_navigator = None
        self.grid_size = grid_size

    def ooda_decide(self, state, possible_actions):
        if self.wp_navigator is None:
            self.wp_navigator = WaypointNavigator(self.agent_id)

        if self.wp_navigator.is_finished():
            self.wp_navigator.reset()
            new_wp = [int(self.rnd_gen.rand() * (self.grid_size[0] - 1)),
                      int(self.rnd_gen.rand() * (self.grid_size[1] - 1))]
            self.wp_navigator.add_waypoint(x=new_wp[0], y=new_wp[1], action=None)

        action, action_kwargs = self.wp_navigator.next_basic_action(state, possible_actions)

        return action, action_kwargs
