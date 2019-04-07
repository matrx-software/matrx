
from visualization.helper_functions import reorder_state_for_GUI

class Visualizer():

    def __init__(self):
        self.agent_states = {}
        self.hu_ag_states = {}
        self.god_state = {}


    def reset(self):
        """ Reset all saved states of (human) agents etc """

        self.states = {}


    def save_state(self, type, id, state, params=None):
        """ Save the filtered agent state which we will visualize later on """

        # add key to states dict
        if type not in self.states:
            self.states[type] = {}

        # add state for specific entity with ID to states dict
        if type == "god":
            self.god_state = state


    def updateGUIs(self, grid_size):
        """
        Update the (human)agent and god views, by sending the updated filtered
        state of each to the Visualizer webserver which will update the
        visualizations.
        """


        # update god
        self.god_state = reorder_state_for_GUI(self.god_state)
        # update agents

        # update human agents

    def visualize(self, grid_size, type):

        # put data in a json array
        data = {'params': {'grid_size': grid_size}, 'states': self.states}
        url = 'http://localhost:3000/update'


        tick_start_time = datetime.datetime.now()

        # send an update of the agent state to the GUI via its API
        r = requests.post(url, json=data)


        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time
        if verbose:
            print("Request + reply took:", tick_duration.total_seconds())
            print("post url:", r.url)

        # handle user_inputs

        self.reset()
        pass
