import numpy as np
import datetime
import requests

class Agent:

    def __init__(self, name, strt_location, action_set, sense_capability, grid_size, properties=None):
        """
        Creates an Agent. All other agents should inherit from this class if you want smarter agents. This agent
        simply randomly selects an action from the possible actions it can do.
        :param name: The name of the agent.
        :param strt_location: The initial location of the agent.
        :param action_set: The actions the agent can perform. A list of strings, with each string a class name of an
        existing action in the package Actions.
        :param sense_capability: A SenseCapability object; it states which object types the agent can perceive within
        what range.
        :param grid_size: The size of the grid. The agent needs to send this along with other information to the
        webapp managing the Agent GUI
        """
        if properties is None:
            self.properties = {"name": name}
        else:
            self.properties = properties.copy()
            self.properties["name"] = name
        self.name = name
        self.location = strt_location
        self.action_set = action_set  # list of Action objects
        self.sense_capability = sense_capability
        self.agent_properties = {}
        self.rnd_seed = None
        self.rnd_gen = None
        self.previous_action = None
        self.previous_action_result = None
        self.grid_size = grid_size

    def get_action(self, state, possible_actions, agent_id):
        """
        The function the environment calls. The environment receives this function object and calls it when it is time
        for this agent to select an action.
        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :param possible_actions: The possible actions the agent can perform according to the grid world. The agent can
        send any other action (as long as it excists in the Action package), but these will not be performed in the
        world resulting in the appriopriate ActionResult.
        :return: An action string, which is the class name of one of the actions in the Action package.
        """

        # send the agent state to the web app GUI
        self.sync_agent_view_GUI(state, agent_id)

        state = self.ooda_observe(state)
        state = self.ooda_orient(state)
        action = self.ooda_decide(state, possible_actions)
        action = self.ooda_act(action)

        return action

    def set_action_result(self, action_result):
        """
        A function that the environment calls (similarly as the self.get_action method) to set the action_result of the
        action this agent decided upon. Note, that the result is given AFTER the action is performed (if possible).
        Hence it is named the self.previous_action_result, as we can read its contents when we should decide on our
        NEXT action after the action whose result this is.
        :param action_result: An object that inherits from ActionResult, containing a boolean whether the action
        succeeded and a string denoting the reason why it failed (if it did so).
        :return:
        """
        self.previous_action_result = action_result

    def get_properties(self):
        """
        Returns all properties you want the grid world to have access to. These are the properties that other agents
        will receive when the observe this agent. Also, these are the properties that will be used to visualize the
        agent.

        By default we add the agent's name to the properties. The grid world is responsible for adding the location to
        it and any other default properties for the AgentAvatar class (the representation of the agent in the grid
        world).

        :return: A dictionary of properties, generally with strings as key and native types as values though is not
        required at all.
        """

        return self.agent_properties


    def set_rnd_seed(self, seed):
        """
        The function that seeds this agent's random seed.
        Currently; the grid world returns a seed for this agent and we need to set it 'manually' in our scenario script.
        In the future this will be done for us by the ScenarioManager.
        :param seed: The random seed this agent needs to be seeded with.
        :return:
        """
        self.rnd_seed = seed
        self.rnd_gen = np.random.RandomState(self.rnd_seed)


    # reorder the state such that it has the x,y coords as keys and can be JSON serialized
    # Old state order: { 'object_name' : {obj_properties}, 'object_name2' : {obj_properties}}
    # New state order: { 'x1_y1') : [obj1, obj2, agent1], 'x2_y1' : [obj1, obj2, agent1]}
    def __reorder_state_for_GUI(self, state):
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


    def sync_agent_view_GUI(self, state, agent_id):
        """
        Send the state of the agent to the webserver such that it can be visualized
        The state
        """

        newState = self.__reorder_state_for_GUI(state)
        print("Agent state reordered:", newState)

        print("Sending update to GUI API for agent %s" % agent_id)

        # put data in a json array
        data = {'params': {'grid_size': self.grid_size}, 'state': newState}

        tick_start_time = datetime.datetime.now()

        # send an update of the agent state to the GUI via its API
        r = requests.post('http://localhost:3000/update/agent/' + agent_id, json=data)

        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time
        print("Request + reply took:", tick_duration.total_seconds())
        print("post url:", r.url)

        # check for errors in the response
        if r.status_code != requests.codes.ok:
            print("Error in contacting GUI API for agent %s" % agent_id)
        else:
            print("Request returned ok. Status code:", r.status_code)


    def ooda_observe(self, state):
        """
        All our agent work through the OODA-loop paradigm; first you observe, then you orient/pre-process, followed by
        a decision process of an action after which we act upon the action.

        This is the Observe phase. In this phase you filter the state further to only those properties the agent is
        actually SUPPOSED to see. Since the grid world returns ALL properties of ALL objects within a certain range(s),
        but perhaps some objects are obscured because they are behind walls, or an agent is not able to see some
        properties an certain objects.

        This filtering is what you do here.

        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :return: A filtered state.
        """
        return state

    def ooda_orient(self, state):
        """
        All our agent work through the OODA-loop paradigm; first you observe, then you orient/pre-process, followed by
        a decision process of an action after which we act upon the action.

        This is the Orient phase. In this phase you can pre-process the state further. For example you can transform it
        in your desired state represantion, or add other knowledge to it you infer from all what is already in the
        state.

        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :return: A filtered state.
        """
        return state

    def ooda_decide(self, state, possible_actions):
        """
        All our agent work through the OODA-loop paradigm; first you observe, then you orient/pre-process, followed by
        a decision process of an action after which we act upon the action.

        This is the Decide phase. In this phase you actually compute your action. For example, this default agent simply
        randomly selects an action from the possible_actions list. However, for smarter agents you need the state
        representation for example to know what a good action is.

        :param state: A state description containing all properties of EnvObject that are within a certain range as
        defined by self.sense_capability. It is a list of properties in a dictionary
        :param possible_actions: A list of strings of the action class names that are possible to do according to the
        grid world. This means that this list contain ALL actions this agent is allowed to do (as in; they are in
        self.action_set) and MAY result in a positive action result. This is not required (e.g.; a remove_object action
        might become impossible if another agent also decided to remove that object and who was a higher in the priority
        list).
        :return: An action string of the class name of an action that is also in self.action_set (it is not required to
        also be in possible_actions, though then the action will automatically fail.)
        """
        if possible_actions:
            action = self.rnd_gen.choice(possible_actions)
        else:
            action = None
        return action

    def ooda_act(self, action):
        """
        All our agent work through the OODA-loop paradigm; first you observe, then you orient/pre-process, followed by
        a decision process of an action after which we act upon the action.

        This is the Act phase. In this phase you might perform a few things that the decided action also causes but is
        not done in and by the grid world itself. For example changing the battery level property of this agent.

        :param action: The decided action that may have additional consequences that are not performed by and in the
        grid world.
        :return: The decided action.
        """
        self.previous_action = action
        return action
