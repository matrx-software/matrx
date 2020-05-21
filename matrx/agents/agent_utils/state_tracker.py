import numpy as np

from matrx.utils import get_distance
import itertools
from matrx.agents.agent_utils.fov import _field_of_view


class StateTracker:

    def __init__(self, agent_id, knowledge_decay=10, fov_occlusion=True):

        # The amount with which we forget known knowledge (we do so linearly)
        if knowledge_decay > 1.0:
            self.__decay = 1 / knowledge_decay
        elif knowledge_decay < 0:
            self.__decay = 0.0
        else:
            self.__decay = knowledge_decay

        # Set the agent's sense capability, needed for FOV occlusion to find the max view radius
        # The sense capability is fetched from the state in the update function
        self.sense_capability = None

        # Whether we occlude objects from view if they are blocked by an intraversable object
        self.fov_occlusion = fov_occlusion

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
        # Decay all objects in our memory
        for obj_id in self.__decay_values.keys():
            self.__decay_values[obj_id] -= self.__decay

        # Check if we need to remove an object
        temp_decay_values = list(self.__decay_values.items()).copy()
        for obj_id, decay in temp_decay_values:
            if decay < 0:
                self.__memorized_state.pop(obj_id)
                self.__decay_values.pop(obj_id)

        # Loop over the given state and update our memorized state
        for obj_id, properties in state.items():
            # the object is new for our memory, previously forgotten or already in our memory and we update it
            self.__memorized_state[obj_id] = properties
            self.__decay_values[obj_id] = 1.0  # (re)set the memory decay

        # Now check if there is an object that we memorized to be at some place we should still be able to perceive but
        # did not find that object there
        self.sense_capability = state[self.agent_id]['sense_capability']  # get the agent's sense capability
        agent_loc = state[self.agent_id]['location']  # get the agent's location
        temp_memorized_state = list(self.__memorized_state.items()).copy()
        for obj_id, properties in temp_memorized_state:
            # We only remove it if it is also not in the given state (since then we updated it just now!)
            if obj_id in state.keys():
                continue

            # Get the location, distance and object class
            loc = properties['location']  # location of memorized object
            distance = get_distance(agent_loc, loc)  # distance to object
            obj_class = properties['class_inheritance'][0]  # type of memorized object

            # Obtain the perceive range for the object
            if obj_class in self.sense_capability:
                perceive_range = self.sense_capability[obj_class]
            elif "*" in self.sense_capability:
                perceive_range = self.sense_capability["*"]
            else:
                perceive_range = -1

            # check if obj is in range and is not in state anymore
            if distance <= perceive_range:
                self.__memorized_state.pop(obj_id)
                self.__decay_values.pop(obj_id)

        return self.get_memorized_state()

    def get_traversability_map(self, inverted=False, state=None):

        if state is None:
            state = self.__memorized_state

        map_size = state['World']['grid_shape']  # (width, height)
        traverse_map = np.array([[int(not inverted) for _ in range(map_size[1])] for _ in range(map_size[0])])
        obj_grid = [[[] for _ in range(map_size[1])] for _ in range(map_size[0])]

        for obj_id, properties in state.items():

            if obj_id == "World":
                continue

            loc = properties['location']

            # we store that there is an object there
            obj_grid[loc[0]][loc[1]].append(obj_id)

            # if another object on that location is intraversable, don't overwrite it
            if (traverse_map[loc[0], loc[1]] == 0 and not inverted) or (traverse_map[loc[0], loc[1]] == 1 and inverted):
                continue

            traverse_map[loc[0], loc[1]] = int(properties['is_traversable']) \
                if not inverted else int(not (properties['is_traversable']))

        return traverse_map, obj_grid

    def __get_occluded_objects(self, state):
        loc = state[self.agent_id]["location"]
        map_size = state['World']['grid_shape']

        radius = max(self.sense_capability.get_capabilities().values())
        if radius >= np.inf:
            radius = max(map_size)

        traverse_grid, obj_grid = self.get_traversability_map(inverted=True, state=state)
        objects_seen = []

        sees = np.zeros(map_size)

        def func_visit_tile(x, y):
            sees[x, y] = 1
            objects_seen.extend(obj_grid[x][y])

        def func_tile_blocked(x, y):
            return bool(traverse_grid[x, y])

        _field_of_view(loc[0], loc[1], map_size[0], map_size[1], radius, func_visit_tile, func_tile_blocked)

        all_objects = list(itertools.chain(*itertools.chain(*obj_grid)))
        occluded_objects = [obj_id for obj_id in all_objects if obj_id not in objects_seen]

        return occluded_objects
