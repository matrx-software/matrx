import numpy as np


class Capability:

    def __init__(self):
        """ Base class for agent capabilities.

        Currently only used for the SenseCapability.

        """
        pass


class SenseCapability(Capability):

    def __init__(self, detectable_objects):
        """This class stores what object types can be perceived in what distance for an agent.

        Parameters
        ----------
        detectable_objects : dict
            A dictionary with as keys the class names of EnvObject and potential inherited classes, and as values the
            distance this object type can be perceived. One can denote the distance for all object types by providing
            a dictionary with None as key, and the desired distance as value.

        Examples
        --------
        An example of a SenseCapability that defines the perception of all AgentBody objects separate from SquareBlock
        objects.

        >>> SenseCapability({"AgentBody": 10, "SquareBlock": 25})

        An example of a SenseCapability that sets the perception range of all objects.

        >>> SenseCapability({None: 25})


        """
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
        """ Returns the dictionary defining what types can be perceived within which distance.

        Returns
        -------
        sense_capabilities: dict
            A dictionary with as keys the object types and values the distances.
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