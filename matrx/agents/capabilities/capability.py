import numpy as np


class Capability:
    """ Private MATRX class.

    Base class for agent capabilities.

    Notes
    -----
    Currently only used for the
    :class:`matrxs.agents.capabilities.capability.SenseCapability`. Might be
    extended in the future to include other type of capabilities.

    """

    def __init__(self):
        pass


class SenseCapability(Capability):
    """ Denotes what an agent can see within a certain range.

    An instance of this class describes to an agent what it can perceive within
    what ranges. It is used by a :class:`matrxs.grid_world.GridWorld` instance
    to construct the agent's state.

    Parameters
    ----------
    detectable_objects : dict
        A dictionary with as keys the class names of EnvObject or inherited
        classes thereof, and as values the distance this object type can be
        perceived.

        If one wants the agent to perceive all object type within some range,
        None can be given as key with the desired range (and other keys are
        ignored).

    Examples
    --------
    An example of a SenseCapability that defines the perception of all agents
    separate from SquareBlock objects. No other objects are perceived.

    >>> SenseCapability({"AgentBody": 10, "SquareBlock": 25})

    An example of a SenseCapability that sets the perception range of all
    objects.

    >>> SenseCapability({None: 25})

    """

    def __init__(self, detectable_objects):
        super().__init__()
        self.__detectable_objects = {}
        for obj_type, sense_range in detectable_objects.items():
            if obj_type is None:
                # If the obj_type is none, we can detect all object types
                self.__detectable_objects = {"*": sense_range}  # hence all other object types in there have no effect
                break  # as such we break this loop
            else:
                self.__detectable_objects[obj_type] = sense_range

    def get_capabilities(self):
        """ Returns the sense capabilities.

        Returns
        -------
        sense_capabilities: dict
            A dictionary with as keys the object types and values the
            distances.

            The key None denotes all object types.
        """
        return self.__detectable_objects.copy()


def create_sense_capability(objects_to_perceive, range_to_perceive_them_in):
    # Check if range and objects are the same length
    assert len(objects_to_perceive) == len(range_to_perceive_them_in)

    # Check if lists are empty, if so return a capability to see all at any range
    if len(objects_to_perceive) == 0:
        return SenseCapability({"*": np.inf})

    # Create sense dictionary
    sense_dict = {}
    for idx, obj_class in enumerate(objects_to_perceive):
        perceive_range = range_to_perceive_them_in[idx]
        if perceive_range is None:
            perceive_range = np.inf
        sense_dict[obj_class] = perceive_range

    sense_capability = SenseCapability(sense_dict)

    return sense_capability
