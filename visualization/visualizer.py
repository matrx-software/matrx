import datetime
import requests

from visualization.helper_functions import reorder_state_for_GUI


class Visualizer():

    def __init__(self, grid_size):
        self.agent_states = {}
        self.hu_ag_states = {}
        self.god_state = {}
        self.verbose = False

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

    def __reorder_state_for_GUI(self, state):
        """
        Reorder the state such that it has the x,y coords as keys and can be JSON serialized
        Old state order: { 'object_name' : {obj_properties}, 'object_name2' : {obj_properties}, ....}
        New state order: { 'x1_y1') : [obj1, obj2, agent1], 'x2_y1' : [obj3, obj4, agent1], ...}
        :param state: state of all visible objects for that entity
        :return: state reordered
        """
        newState = {}
        for obj in state:

            # convert the [x,y] coords to a x_y notation so we can use it as a key which is
            # also JSON serializable
            strXYkey = str(state[obj]['location'][0]) + "_" + str(state[obj]['location'][1])

            # create a new list with (x,y) as key if it does not exist yet in the newState dict
            if strXYkey not in newState:
                newState[strXYkey] = []

            # add the object or agent to the list at the (x,y) location in the dict
            newState[strXYkey].append( state[obj] )

        return newState


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


    def updateGUIs(self):
        """
        Update the (human)agent and god views, by sending the updated filtered
        state of each to the Visualizer webserver which will update the
        visualizations.
        """

        # reorder god state
        self.god_state = self.__reorder_state_for_GUI(self.god_state)

        # reorder agents state
        for agent_id in self.agent_states:
            self.agent_states[agent_id] = self.__reorder_state_for_GUI(self.agent_states[agent_id])

        # reorder human states
        for hu_ag_id in self.hu_ag_states:
            self.hu_ag_states[hu_ag_id] = self.__reorder_state_for_GUI(self.hu_ag_states[hu_ag_id])

        # send the update to the webserver
        self.__sendGUIupdate()


    def __sendGUIupdate(self):
        """
        Send the states of all (human)agents and god to the webserver for updating of the GUI
        """

        # put data in a json array
        data = {'god': self.god_state, 'agent_states': self.agent_states, 'hu_ag_states': self.hu_ag_states}
        url = 'http://localhost:3000/update'

        tick_start_time = datetime.datetime.now()

        # send an update of the agent state to the GUI via its API
        r = requests.post(url, json=data)


        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time
        if self.verbose:
            print("Request + reply took:", tick_duration.total_seconds())
            print("post url:", r.url)

        # handle user_inputs

        self.reset()
        pass
