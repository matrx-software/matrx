import datetime
import requests

from visualization.helper_functions import reorder_state_for_GUI

class Visualizer():

    def __init__(self, grid_size):
        self.agent_states = {}
        self.hu_ag_states = {}
        self.god_state = {}

        self.__initGUI(grid_size=grid_size, verbose=False)


    def __initGUI(self, grid_size, verbose):
        """
        Send an initialization message to the GUI webserver, which sends the grid_size.
        """
        data = {'params': {'grid_size': grid_size} }

        url = 'http://localhost:3000/init'

        tick_start_time = datetime.datetime.now()

        # send an update of the agent state to the GUI via its API
        r = requests.post(url, json=data)

        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time
        if verbose:
            print("Request + reply took:", tick_duration.total_seconds())
            print("post url:", r.url)

        # check for errors in the response
        if r.status_code != requests.codes.ok:
            print("Error in initializing GUI")



    def reset(self):
        """ Reset all saved states of (human) agents etc """

        self.agent_states = {}
        self.hu_ag_states = {}
        self.god_state = {}


    def save_state(self, type, id, state, params=None):
        """ Save the filtered agent state which we will visualize later on """

        print(f"Saving state in visualizer for type {type} and id {id} and state")
        # print(state)

        # add state for specific entity with ID to states dict
        if type == "god":
            self.god_state = state
        elif type == "agent":
            self.agent_states[id] = state
        elif type == "humanagent":
            self.hu_ag_states[id] = state


    def updateGUIs(self):
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
