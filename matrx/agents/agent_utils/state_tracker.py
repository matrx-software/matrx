import warnings

import numpy as np

from matrx.utils import get_distance
import itertools
from matrx.agents.agent_utils.fov import _field_of_view


class StateTracker:
    """ The tracker of agent observations over ticks.

    .. deprecated:: 2.0.7
        `StateTracker` will be removed in a future MATRX version where it will be fully replaced by `State`.

    """

    def __init__(self, agent_id, knowledge_decay=10, fov_occlusion=True):
        """ Create an instance to track an agent's observations over ticks.

        Parameters
        ----------
        agent_id : str
            The agent id this tracker is linked to.
        knowledge_decay : int
            For how many ticks observations need to be remembered when not observed.
        fov_occlusion : bool
            Whether intraversable objects should block the agent's field of view or not.

        .. deprecated:: 2.0.7
            `StateTracker` will be removed in MATRX v2.2 and fully replaced by `State`.

        Warnings
        --------
        The `fov_occlusion` is a very unstable feature not fully tested. Use at your own risk!

        """

        warnings.warn(
            "The StateTracker will be deprecated in a future version of MATRX, replaced by State.",
            PendingDeprecationWarning
        )

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
        """ Sets the number of ticks the tracker should memorize unobserved objects.

        Parameters
        ----------
        knowledge_decay : int
            The number of ticks an unobserved object is memorized.

        """
        self.__decay = knowledge_decay

    def get_memorized_state(self):
        """ Returns the memorized state so far.

        Returns
        -------
        dict
            The dictionary containing all current and memorized observations.

        """
        return self.__memorized_state.copy()

    def update(self, state):
        """ Updates this tracker with the new observations.

        This method also removes any past observations that are needed to be forgotten by now.

        Parameters
        ----------
        state : dict
            The state dictionary containing an agent's current observations.

        Returns
        -------
        dict
            The dictionary containing all current and memorized observations.

        """
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

    def __get_occluded_objects(self, state):
        """ A private MATRX method.

        Applies the Field of View (FOV) algorithm.

        Parameters
        ----------
        state : dict
            The dictionary representing the agent's (memorized) observations to be used to create the map.

        Returns
        -------
        list
            The list of objects that are being occluded by other objects.

        """
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

def get_traversability_map(state=None, inverted=True):
    """ Returns a map where the agent can move to. Traversability is binary.

    This map is based on the provided state dictionary that might represent the observations of an agent. Since
    these observations can be limited in sense of range and accuracy, the map might not be truthful to what is
    actually possible. This mimics the fact that an agent only knows what it can observe and infer from those
    observations.

    Parameters
    ----------
    inverted : bool (Default: False)
        Whether the map should be inverted (signalling where the agent cannot move to).
    state : dict
        The dictionary representing the agent's (memorized) observations to be used to create the map.

    Returns
    -------
    array
        An array of shape (width,height) equal to the grid world's size. Contains a 1 on each (x,y) coordinate where
        the agent can move to (a 0 when inverted) and a 0 where it cannot move to (a 1 when inverted).
    list
        A list of lists with the width and height of the gird world as size. Contains on each (x,y) coordinate the
        object ID if any according to the provided state dictionary.

    """

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

def get_weighted_traversability_map(state=None):
    """ Returns a weighted map where the agent can move to. 

    This map is based on the provided state dictionary that might represent the observations of an agent. Since
    these observations can be limited in sense of range and accuracy, the map might not be truthful to what is
    actually possible. This mimics the fact that an agent only knows what it can observe and infer from those
    observations.
    Traversability is weighted based on the the traversability of that object, and in addition the `traversability_penatly` property 
    (if available) which describes the (speed) penatly of moving over this object. The `traversability_penatly` is between 0 (no penalty) and 1 (max penalty)

    Parameters
    ----------
    inverted : bool (Default: False)
        Whether the map should be inverted (signalling where the agent cannot move to).
    state : dict
        The dictionary representing the agent's (memorized) observations to be used to create the map.

    Returns
    -------
    array
        An array of shape (width,height) equal to the grid world's size. Contains a 0 on each (x,y) coordinate where
        the agent can move to 1 where it cannot move to. Contains any integer between 0 and 1 that indicates a preference.
    list
        A list of lists with the width and height of the gird world as size. Contains on each (x,y) coordinate the
        object ID if any according to the provided state dictionary.

    """

    map_size = state['World']['grid_shape']  # (width, height)
    traverse_map = np.array([[0.0 for _ in range(map_size[1])] for _ in range(map_size[0])])
    obj_grid = [[[] for _ in range(map_size[1])] for _ in range(map_size[0])]

    for obj_id, properties in state.items():

        if obj_id == "World":
            continue

        loc = properties['location']

        # we store that there is an object there
        obj_grid[loc[0]][loc[1]].append(obj_id)
        
        # check if the object is traversable
        traversability = int(not properties['is_traversable']) * 1.0

        # if it is traversable, check if the user specified a preference with the `traversability_penatly` property for this object 
        # higher penalty is less preferable 
        if (traversability < 1) and ('traversability_penalty' in properties):
            traversability = properties['traversability_penalty']

        # the traversability of a location is equal to its least traversable object on there 
        if traversability > traverse_map[loc[0], loc[1]]:
            traverse_map[loc[0], loc[1]] = traversability

    return traverse_map, obj_grid