import numpy as np


class Agent:

    def __init__(self, name, strt_location, possible_actions, sense_capability):
        self.name = name
        self.location = strt_location
        self.possible_actions = possible_actions  # list of Action objects
        self.sense_capability = sense_capability
        self.agent_properties = {}
        self.rnd_seed = None
        self.rnd_gen = None
        self.current_action = None
        self.last_action = None
        self.current_action_result = None
        self.last_action_result = None

    def get_action(self, state, possible_actions):
        self.last_action_result = self.current_action_result
        self.current_action_result = None
        action = self.define_action(state, possible_actions)
        return action

    def set_action_result(self, action_result):
        self.current_action_result = action_result

    def get_properties(self):
        return self.agent_properties

    def set_rnd_seed(self, seed):
        self.rnd_seed = seed
        self.rnd_gen = np.random.RandomState(self.rnd_seed)

    def define_action(self, state, possible_actions):
        pass

    def filter_state(self, state):
        # TODO
        pass


class RandomAgent(Agent):

    def __init__(self, name, strt_location, possible_actions, sense_capability):
        super().__init__(name, strt_location, possible_actions, sense_capability)

    def define_action(self, state, possible_actions):
        self.last_action = self.current_action
        if possible_actions:
            self.current_action = self.rnd_gen.choice(possible_actions)
        else:
            self.current_action = None
        return self.current_action
