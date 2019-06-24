import datetime
import requests
import numpy as np
import copy

from agents.agent import Agent
from agents.human_agent import HumanAgent
from collections import OrderedDict


class Visualizer():
    '''
    The Visualizer class bridges the gap between the Gridworld simulation environment, and
    the Flask webserver which does the visualization. This is done by keeping track
    of the states of every agent, human-agent, and the complete (god) state for every
    simulation iteration, and sending these to the Flask webserver via an API where they are visualized.
    '''

    def __init__(self, grid_size, vis_bg_clr):
        self.agent_states = {}
        self.hu_ag_states = {}
        self.god_state = {}
        self.verbose = False
        self.userinputs = {}

        self.__initGUI(grid_size=grid_size, vis_bg_clr=vis_bg_clr)


    def __initGUI(self, grid_size, vis_bg_clr):
        """
        Send an initialization message to the GUI webserver, which sends the grid_size.
        """
        data = {'params': {'grid_size': grid_size, 'vis_bg_clr': vis_bg_clr}}

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


    def save_state(self, inheritance_chain, id, state, params=None):
        """ Save the filtered agent state which we will visualize later on """

        # prepare the state for the GUI
        GUIstate = self.__reorder_state_for_GUI(state)
        GUIstate = self.__filter_state(GUIstate)

        # add state for specific entity with ID to states dict
        if isinstance(inheritance_chain, list):
            for c in inheritance_chain:
                if c == Agent.__name__:
                    self.agent_states[id] = GUIstate
                elif c == HumanAgent.__name__:
                    self.hu_ag_states[id] = GUIstate
        else:
            self.god_state = GUIstate


    def __filter_state(self, state):
        """
        Filter values from the state dictionary which cannot be converted to json,
        such as np.inf
        """
        # loop through the dictionary
        for key, value in state.items():
            # check subdict
            if type(value) == dict:
                state[key] = self.__filter_state(value)

            # otherwise check the value
            else:
                # numpy inf is not recognized as an integer in javascript, so replace it with -1
                if value == np.inf:
                    state[key] = -1

        return state


    def __reorder_state_for_GUI(self, state):
        """
        Convert the state, which is a dictionary of objects with object ID as key,
        into a new dictionary with as key the visualization depth, and as value
        the objects which are to be displayed at that depth
        """
        new_state = {}

        # loop through all objects in the state
        for objID, obj in state.items():
            # fetch the visualization depth
            visDepth = state[objID]["visualization"]['depth']

            if "sense_capability" in obj:
                obj["sense_capability"] = str(obj["sense_capability"])

            # save the object in the new_state dict at its visualization_depth
            if visDepth not in new_state:
                new_state[visDepth] = {}

            # add the object or agent to the list at the (x,y) location in the dict
            new_state[visDepth][objID] = obj

        # sort dict on depth
        sorted_state = {}
        for depth in sorted(new_state.keys()):
            sorted_state[depth]= new_state[depth]

        return sorted_state


    def update_guis(self, tick):
        """
        Update the (human)agent and god views, by sending the updated filtered
        state of each to the Visualizer webserver which will update the
        visualizations.
        """
        self.tick = tick
        # send the update to the webserver
        self.__send_gui_update()


    def __send_gui_update(self):
        """
        Send the states of all (human)agents and god to the webserver for updating of the GUI
        """

        # put data in a json array
        data = {'god': self.god_state, 'agent_states': self.agent_states, 'hu_ag_states': self.hu_ag_states,
                'tick': self.tick}
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
        elif self.verbose:
            print("User input received:", repl)

        # otherwise return the userinput
        self.userinputs = repl
