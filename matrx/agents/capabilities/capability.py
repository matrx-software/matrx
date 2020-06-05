import numpy as np


class Capability:
    """ Denotes an capability of an agent.

    Base class for agent capabilities.

    Notes
    -----
    Currently only used for the
    :class:`matrx.agents.capabilities.capability.SenseCapability`. Might be
    extended in the future to include other type of capabilities.

    """

    def __init__(self):
        pass


class SenseCapability(Capability):
    """ Denotes what an agent can see within a certain range.

    An instance of this class describes to an agent what it can perceive within
    what ranges. It is used by a :class:`matrx.grid_world.GridWorld` instance
    to construct the agent's state.

    To limit agents to sense objects more granulary then the given object types
    allow for, you can extend classes with your own classes. For example, one
    can extend the `SquareBlock` class into a custom class called
    `MySquareBlock`. This allows you to specify these two types separately to
    an agent for perception.

    Examples
    --------
    An example of a SenseCapability that defines the perception of all agents
    separate from SquareBlock objects. No other objects are perceived.

    >>> from matrx.objects import AgentBody, SquareBlock
    >>> SenseCapability({AgentBody: 10, SquareBlock: 25})

    An example of a SenseCapability that sets the perception range of all
    objects.

    >>> SenseCapability({None: 25})

    An example of a SenseCapability that sets the range of perceiving all
    other agents to 25 but the perception of all other objects to 10.

    >>> from matrx.objects import AgentBody
    >>> SenseCapability({AgentBody: 25, None: 10})

    """

    def __init__(self, detectable_objects):
        """ Denotes what an agent can see within a certain range.

        Parameters
        ----------
        detectable_objects : dict
            A dictionary with as keys the class you wish to perceive, and as
            values the distance this object type can be perceived. The None
            key stands for all otherwise not specified object types.
        """

        super().__init__()
        self.__detectable_objects = {}
        for obj_type, sense_range in detectable_objects.items():
            if obj_type is None:
                # If the obj_type is none, we can detect all object types in that associated range who have not a
                # specific range set.
                self.__detectable_objects["*"] = sense_range
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
    """ Creates a sense capability based that denotes what object types can be perceived from what range.


    Parameters
    ----------
    objects_to_perceive : list
        Various types of objects that the agent can perceive. An empty list is interpreted as all objects being
        detectable with infinite range by the agent.

    range_to_perceive_them_in : list
        The range for the object in `objects_to_perceive` from which the agent can perceive that object type.
        So range_to_perceive_them_in[4] denotes the range from which the agent can detect the object
        at objects_to_perceive[4].

    """
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
