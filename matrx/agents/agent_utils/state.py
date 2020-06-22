import copy
from collections import Iterable, MutableMapping

from matrx import utils
from matrx.objects import Door, AreaTile, Wall


class State(MutableMapping):

    def __init__(self, memorize_for_ticks=None):
        if memorize_for_ticks is None:
            self.__decay_val = 0
        else:
            self.__decay_val = 1.0 / memorize_for_ticks

        self.__state_dict = {}
        self.__prev_state_dict = {}
        self.__decays = {}

    def state_update(self, state_dict):
        prev_state = self.__state_dict.copy()
        state = state_dict.copy()

        # Get the ids of all newly perceived objects
        new_ids = set(state.keys()) - set(prev_state.keys())

        # Get the ids of all objects that were perceived before as well
        persistent_ids = set(state.keys()) - new_ids

        # Get the ids of all objects that are not perceived any more
        gone_ids = set(prev_state.keys()) - set(state.keys())

        # Handle knowledge decay if decay actually matters (e.g. that stuff need to be memorized)
        if self.__decay_val > 0:
            # Decay the decays of all objects that are not perceived any longer
            for obj_id in gone_ids:
                self.__decays[obj_id] = max((self.__decays[obj_id] - self.__decay_val), 0)

            # Reset the decays of all objects that are still perceived
            for obj_id in persistent_ids:
                self.__decays[obj_id] = 1.0

            # Add all new decays of the newly perceived objects
            for obj_id in new_ids:
                self.__decays[obj_id] = 1.0

            # Check for non-zero decays and flag them for keeping (this now also includes all new_ids as we just added
            # them).
            to_keep_ids = []
            for obj_id, decay in self.__decays.items():
                if decay > 0:
                    to_keep_ids.append(obj_id)
                else:  # remove all zero decay objects, this reduces the self.__decays of growing with zero decays
                    self.__decays.pop(obj_id)
            to_keep_ids = set(to_keep_ids)

        # If decay does not matter, flag all objects for keeping that are newly or still perceived
        else:
            to_keep_ids = new_ids.union(persistent_ids)

        # Create new state
        new_state = {}
        for obj_id in to_keep_ids:
            # If the object id is in the received state, pick that one. This makes sure that any objects that were also
            # in the previous state get updated with newly perceived properties
            if obj_id in state.keys():
                new_state[obj_id] = state[obj_id]
            # If the object id is not in the received state, it may still be in the previous state (e.g. because its
            # decay was non-zero). Though this only happens when decay is set.
            elif obj_id in prev_state.keys():
                new_state[obj_id] = prev_state[obj_id]

        # Set the new state
        self.__prev_state_dict = self.__state_dict
        self.__state_dict = new_state
        # self.update(dict(*args, **kwargs))  # use the free update to set keys

        # Return self
        return self

    ###############################################
    # Methods that allow State to be used as dict #
    ###############################################
    def __getitem__(self, key):
        """ Returns all state objects that comply with the given key.

        This method overrides a dict's __getitem__, used in bracket notation, e.g. some_dict[key]. It allows us to
        create a dict that can obtain its items based on more than a single key. It supports the following as keys:

        - A regular key in `state.keys()`. If the key is found, returns that single object.
        - An iterable of keys in `state.keys()`. If *all* keys are found, returns all objects.
        - A string representing a property name. Returns a list of all objects with that property.
        - An iterable of property names. Returns a list of objects that contain all given properties.
        - A dictionary of type {property_name: property_value, ...}. Returns all objects that have all those specified
        property names with their respective property value.
        - A dictionary of type {property_name: [property_value, ...] ...}. Returns all objects that have all those
        specified property names and one of their respective given property value options. This can be mixed with
        property names and values as list or single value (e.g. {name_1: [value_1a, value_1b], name_2: value_2}.

        This allows for a highly versatile search in the perceived state. However, its complexity might be daunting and
        State offers numerous helper methods that make your life simpler. For instance, state.get_with_property(props)
        wraps this method and calls `self[props]

        Parameters
        ----------
        key : str, list, dict
            The key for which we search the state. When a string, it first assumes it is an object ID and if it can't
            find any, assumes it is a property name and finds all objects that have it. If it is a list, it first
            assumes a list of object IDs if not all are object IDs it assumes a list of property names. If a dict, it
            assumes it is of shape {property_name: property_value, ...} or {property_name: [allowable_value, ...], ...}.

        Returns
        -------
        dict, list
            Returns a dict representing the object if only one object was found. If more objects are found, returns a
            list of them. Returns None when no object was found.

        Raises
        ------
        KeyError
            When nothing can be found.

        Examples
        --------
        The examples below assume a world containing several rooms named room_0, room_1 and room_2 containing tiles,
        walls and doors. There are also some other agents and SquareBlock objects.

        Find the agent with the ID 'agent_0`.
        >>> state["agent_0"]

        Find the blocks with the IDs of 'block_321' and 'block_543'
        >>> state[['block_321', 'block_543']]

        Find all objects with the property 'is_open' (e.g. doors)
        >>> state['is_open']

        Find all objects with the property 'is_open' and value 'True' (all open doors)
        >>> state[{'is_open': True}]

        Find all objects with the property 'room_name' and value 'room_0' but also with the property 'class_inheritance'
         and value 'Wall' (e.g. all walls of room_0)
        >>> state['room_name': 'room_0', 'class_inheritance': 'Wall']

        Find all open doors of room_0.
        >>> state[{'room_name': 'room_0', 'class_inheritance': 'Door', 'is_open': 'True'}]

        Find all objects that are either a Wall or Door.
        >>> state['class_inheritance': ['Wall', 'Door']]

        It works for any property, including custom properties: Given a custom property 'foo' and a possible value 'b',
        'a' or 'r', find all objects with value 'b' and 'a'.
        >>> state['foo': ['b', 'a']]

        It works for any possible value (except for dict, see Notes).
        >>> state['number': [1, 2], 'some_list': [['a', 1], ['b', 2]]]

        Notes
        -----
        In case a passed property value is an iterable, it searches whether that iterable is *part* of an objects value
        for that property.

        E.g. state[{'some_list': ['a', 1]}] will also return an object with obj['some_list'] = ['a', 'b', 1, 2]}

        Warnings
        --------
        You cannot find any objects with a property name whose values are a dict. This means you cannot (as of now) use
        this method to find all objects with a certain colour using something as:

        `state[{'visualization': {'colour': '#000000'}}]`

        Instead of returning all objects that are black, it returns all objects with a 'visualization' property that
        contains the key 'colour' (which is basically every object). All objects that do not have the 'visualization'
        property or do have it but not with the key 'colour' in it, are ignored.

        The 'visualization' property is one such example. But MATRX allows to add custom properties whose values are
        dicts. Currently, there is no method to quickly find these using State. Instead you should rely on finding it
        yourself.

        If you want to locate objects with certain visualization properties, we offer several helper methods to do so.
        These are; state.get_with_colour(...), state.get_with_size(...), state.get_with_shape(...),
        state.get_with_depth(...), and state.get_with_opacity(...).
        """
        found_objects = self.__find_object(props=key, combined=True)
        if found_objects is not None and len(found_objects) == 1:  # just a single object
            return found_objects[0]
        return found_objects

    def __setitem__(self, key, value):
        raise ValueError("You cannot set items to the state, use state.state_update(...) instead.")

    def __delitem__(self, key):
        del self.__state_dict[key]

    def __iter__(self):
        return iter(self.__state_dict)

    def __len__(self):
        return len(self.__state_dict)

    def update(self, *args, **kwargs):
        raise ValueError("You cannot update the state, use state.state_update(...) instead.")

    def copy(self):
        return copy.deepcopy(self)

    def pop(self, obj_id):
        return self.__state_dict.pop(obj_id)

    def remove(self, obj_id):
        self.__state_dict.pop(obj_id)

    def as_dict(self):
        return self.__state_dict

    ###############################################
    #     Some helpful getters for the state      #
    ###############################################
    def get_with_property(self, props, combined=True):
        found = self.__find_object(props, combined)
        return found

    def get_world_info(self):
        return self.__state_dict['World']

    def remove_with_property(self, props, combined=True):
        found = self.__find_object(props, combined)
        _ = (self.remove(obj['obj_id']) for f in found for obj in f)

    def get_of_type(self, obj_type):
        return self.get_with_property("class_inheritance", obj_type)

    def get_room_objects(self, room_name):
        return self.get_with_property("room_name", room_name)

    def get_all_room_names(self):
        return list({obj['room_name'] for obj in self.get_with_property("room_name")})

    def get_room_content(self, room_name):
        # Locate method to identify room content
        def is_content(obj):
            if 'class_inheritance' in obj.keys():
                chain = obj['class_inheritance']
                if not (Wall.__name__ in chain or Door.__name__ in chain or AreaTile in chain):
                    return obj
            else:  # the object is a Wall, Door or AreaTile
                return None

        # Get all walls of the room
        walls = self.get_with_property(["room_name", "class_inheritance"], [room_name, "Wall"], combined=True)

        # Get the top left corner and width and height of the room based on the found walls (and assuming the room is
        # rectangle).
        xs = [wall['location'][0] for wall in walls]
        ys = [wall['location'][1] for wall in walls]
        top_left = (min(xs), min(ys))
        width = max(xs) - top_left[0] + 1
        height = max(ys) - top_left[1] + 1
        content_locs = utils.get_room_locations(top_left, width, height)

        # Get all objects with those content locations
        content = self.get_with_property('location', content_locs)

        # Get all room objects
        room_objs = self.get_room_objects(room_name)

        # Filter out all area's, walls and doors
        content = map(is_content, room_objs)
        content = [c for c in content if c is not None]

        return content

    def get_room_doors(self, room_name):
        # Locate method to identify doors
        def is_content(obj):
            if 'class_inheritance' in obj.keys():
                chain = obj['class_inheritance']
                if Door.__name__ in chain:
                    return obj
            else:  # the object is not a Door
                return None

        room_objs = self.get_room_objects(room_name)
        # Filter out all doors
        doors = map(is_content, room_objs)
        doors = [c for c in doors if c is not None]

        return doors

    def get_agents(self):
        pass

    def get_agent_with_property(self, prop_name, prop_value):
        pass

    def get_team_members(self):
        pass

    def get_closest_object(self):
        pass

    def get_closest_with_property(self, prop_name, prop_value):
        pass

    def get_closest_room(self):
        pass

    def get_closest_agent(self):
        pass

    def get_with_colour(self, colour):
        pass

    def get_with_size(self, size):
        pass

    def get_with_shape(self, shape):
        pass

    def get_with_depth(self, depth):
        pass

    def get_with_opacity(self, opacity):
        pass

    ###############################################
    # Some higher level abstractions of the state #
    ###############################################
    def get_traverse_map(self):
        pass

    def get_distance_map(self):
        pass

    def apply_occlusion(self):
        pass

    ##################################################
    # The basic functions that make up most of state #
    ##################################################
    def __find_object(self, props, combined):
        # Make sure that props is a dict, with as keys the property names and as values a tuple of allowable property
        # values (which can be (None,) if no value is specified).
        if isinstance(props, dict):
            # if props is a dict, we check if its values are tuples and cast them to tuples when there are any iterable
            # and wrap them in a tuple if it is a single value.
            props = {p: v if isinstance(v, tuple) else tuple(v) if State.__is_iterable(v) else tuple([v])
                     for p, v in props.items()}
        elif isinstance(props, str):  # props is a single string
            # It could be that props is in fact an "obj_id", the only value allowed to be passed and return something so
            # we check if it is in our dict and return it.
            if props in self.__state_dict.keys():
                found = [self.__state_dict[props]]
                return found
            # props is a single property, so make a appropriate dict out of it with no value
            props = {props: (None, )}
        elif State.__is_iterable(props):
            # props is a list, and it may be a list of object ids so first check if this is the case
            found = [self.__state_dict[obj_id] for obj_id in props if obj_id in self.__state_dict.keys()]
            if len(found) != len(props):  # if one given prop_name was not an actual obj_id, treat all as property names
                # props is a list, assuming a list of property names.
                props = {p: (None,) for p in props}
            else:  # all property names were in fact keys, so return what we found
                return found

        # For each prop_name, prop_value combination, find the relevant objects. If there are more than one allowable
        # property value, search for those as well.
        found = [[self.__find(name, val) for val in vals] for name, vals in props.items()]

        # Check if we searched for more than one property
        if len(props) > 1:
            # If we just want all objects with EITHER property (potentially with the set value), we just flatten the
            # list (prop names) of lists (prop values).
            if not combined:
                # we know we have multiple property names, so we flatten in that dimension
                found = [value_found for sub_found in found for value_found in sub_found]
                # know we also flatten in the property value dimension, resulting in one big list of all objects that
                # have the specified property name and property values
                found = [obj for value_found in found for obj in value_found]

            # If we want all objects that have ALL the properties (potentially also with their respective value), we
            # select those objects that are in all sub-lists
            else:
                # We transform all lists of objects that adhere to each property name (and possible value) to a set
                sets = [set(obj['obj_id'] for obj_list in sub_found for obj in obj_list) for sub_found in found]

                # Next we loop over each set, and consequtively take the intersection of each set. E.g. we start with
                # the first set as the intersection, and set it to the intersection of the previous intersect and next
                # set,
                intersect = set(sets[0])
                for s in sets[1:]:
                    intersect = intersect.intersection(s)

                # Now we have all the object ids, but we want the objects. So if the intersection is not empty, we
                # transform all found objects to a single dict with their ids as keys. Next we loop through every id and
                # retrieve the object dict that belongs to it.
                if len(intersect) > 0:
                    full_dict = {obj['obj_id']: obj for sub_found in found for obj_list in sub_found for obj in
                                 obj_list}
                    found = [full_dict[obj_id] for obj_id in intersect]
                else:
                    found = []
        else:  # just one property name given
            found = found[0]  # take that property name list
            if len(list(props.values())[0]) > 1:  # we have more than one property values given
                # flatten the list
                found = [obj for f in found for obj in f]
            elif len(found[0]) == 0:  # if just one property value was given (or omitted) but nothing was found
                found = None

        # If nothing was found, we set it to None for easy identification and break any iterable over it.
        if not found:
            found = None

        return found

    def __find(self, prop_name, prop_value=None):
        # A local function that identifies whether a given obj_id-obj pair has the requested property name and, if
        # given, the right property value. Is used in the map method to find all object that adhere to it.
        def locate(id_obj_pair):
            obj = id_obj_pair[1]

            # The object is found when it has the property and the value is none, or when it has the property and the
            # requested value is the value of that property OR is in that value of that property (e.g. as substring or
            # list item).
            if prop_name in obj:
                # value given and equals that in the object
                if prop_value is None or prop_value == obj[prop_name]:
                    return obj
                # value given and is in that object's property (e.g. as substring of item in list)
                elif prop_value is not None and isinstance(obj[prop_name], Iterable) and prop_value in obj[prop_name]:
                    return obj
            return None

        # try to locate it in the regular dict as an object id, this allows us to use this method also to quickly locate
        # objects based on their object ID.
        try:
            return self.__state_dict[prop_value]
        # if the prop value was not a key in the dict (or simply None), find all objects with that property and value if
        # given. This uses Python's map function to bring our search to C.
        except KeyError:
            located = map(locate, self.__state_dict.items())
            return [l for l in located if l is not None]  # only return the found objects

    @staticmethod
    def __is_iterable(arg):
        # Checks if the arg functions as an iterable (e.g. is a list, tuple, set, dict, etc.). The isinstance method
        # would be less specific or very large to include all desirable types. Since, isinstance(arg, Iterable) would
        # also pass for any strings, but isinstance(arg, (list, tuple, dict, set, array, ...)) grows quite large.
        return not hasattr(arg, "strip") and (hasattr(arg, "__getitem__") or hasattr(arg, "__iter__"))
