import numpy as np

from environment.helper_functions import get_distance


class StateTracker:

    def __init__(self, agent_id, knowledge_decay=10):

        # The amount with which we forget known knowledge (we do so linearly)
        if knowledge_decay > 1.0:
            self.__decay = 1 / knowledge_decay
        elif knowledge_decay < 0:
            self.__decay = 0.0
        else:
            self.__decay = knowledge_decay

        # We store the agent id of which we track the state so we know what object in the state belongs to the agent
        self.agent_id = agent_id

        # here we store our information, a regular state dict
        self.__memorized_state = {}
        # our dict in which we keep track of the decays of each object
        self.__decay_values = {}

    def set_knowledge_decay(self, knowledge_decay):
        self.__decay = knowledge_decay

    def get_memorized_state(self):
        return self.__memorized_state.copy()

    def update(self, state):

        # Update all of the objects decays
        for id in self.__decay_values.keys():
            self.__decay_values[id] -= self.__decay

        # Check if we need to remove an object
        temp_decay_values = list(self.__decay_values.items()).copy()
        for id, decay in temp_decay_values:
            if decay < 0:
                self.__memorized_state.pop(id)
                self.__decay_values.pop(id)

        # Loop over the given state and update our memorized state
        for id, properties in state.items():
            # the object is new for our memory, previously forgotten or already in our memory and we update it
            self.__memorized_state[id] = properties
            self.__decay_values[id] = 1.0  # (re)set the memory decay

        # Now check if there is an object that we memorized to be at some place we should still be able to perceive but
        # did not find that object there
        sense_capability = state[self.agent_id]['sense_capability']  # get the agent's sense capability
        agent_loc = state[self.agent_id]['location']  # get the agent's location
        temp_memorized_state = list(self.__memorized_state.items()).copy()
        for id, properties in temp_memorized_state:
            # We only remove it if it is also not in the given state (since then we updated it just now!)
            if id in state.keys():
                continue

            # Get the location, distance and object class
            loc = properties['location']  # location of memorized object
            distance = get_distance(agent_loc, loc)  # distance to object
            obj_class = properties['class_inheritance'][0]  # type of memorized object

            # Obtain the perceive range for the object
            if obj_class in sense_capability:
                perceive_range = sense_capability[obj_class]
            elif "*" in sense_capability:
                perceive_range = sense_capability["*"]
            else:
                perceive_range = -1

            # check if obj is in range and is not in state anymore
            if distance <= perceive_range:
                self.__memorized_state.pop(id)
                self.__decay_values.pop(id)

        return self.get_memorized_state()

    def get_traversability_map(self, inverted=False):
        map_size = self.__memorized_state['World']['grid_shape']
        traverse_map = np.array([[int(not inverted) for _ in range(map_size[1])] for _ in range(map_size[0])])

        for id, properties in self.__memorized_state.items():

            if id == "World":
                continue

            loc = properties['location']
            traverse_map[loc[0], loc[1]] = int(properties['is_traversable']) \
                if not inverted else int(not(properties['is_traversable']))

        return traverse_map