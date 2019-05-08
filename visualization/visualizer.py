import datetime
import requests

class Visualizer():
    '''
    The Visualizer class bridges the gap between the Gridworld simulation environment, and
    the Flask webserver which does the visualization. This is done by keeping track
    of the states of every agent, human-agent, and the complete (god) state for every
    simulation iteration, and sending these to the Flask webserver via an API where they are visualized.
    '''

    def __init__(self, grid_size):
        self.agent_states = {}
        self.hu_ag_states = {}
        self.god_state = {}
        self.verbose = False
        self.userinputs = {}

        self.__initGUI(grid_size=grid_size)


    def __initGUI(self, grid_size):
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
        if self.verbose:
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

        # add state for specific entity with ID to states dict
        if type == "god":
            self.god_state = state
        elif type == "agent":
            self.agent_states[id] = state
        elif type == "humanagent":
            self.hu_ag_states[id] = state


    def updateGUIs(self, tick):
        """
        Update the (human)agent and god views, by sending the updated filtered
        state of each to the Visualizer webserver which will update the
        visualizations.
        """
        self.tick = tick
        # send the update to the webserver
        self.__sendGUIupdate()




    def __sendGUIupdate(self):
        """
        Send the states of all (human)agents and god to the webserver for updating of the GUI
        """

        # put data in a json array
        data = {'god': self.god_state, 'agent_states': self.agent_states, 'hu_ag_states': self.hu_ag_states, 'tick': self.tick}
        url = 'http://localhost:3000/update'

        tick_start_time = datetime.datetime.now()

        # send an update of the agent state to the GUI via its API
        r = requests.post(url, json=data)


        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time
        if self.verbose:
            print("Request + reply took:", tick_duration.total_seconds())
            print("post url:", r.url)

        # reset saved states
        self.reset()

        # check if there was any user input for a human agent
        repl = r.json()

        if self.verbose:
            print("User inputs received:")
            print(repl)

        # return None if there was no userinput
        if repl == {}:
            self.userinputs = {}
        else:
            print("User input received:", repl)

        # otherwise return the userinput
        self.userinputs = repl
