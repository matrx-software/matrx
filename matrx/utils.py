import itertools
import math


def get_distance(coord1, coord2):
    """ Get distance between two x,y coordinates """
    dist = [(a - b) ** 2 for a, b in zip(coord1, coord2)]
    dist = math.sqrt(sum(dist))
    return dist


def get_room_locations(room_top_left, room_width, room_height):
    """ Returns the locations within a room, excluding walls.

    This is a helper function for adding objects to a room. It returns a
    list of all (x,y) coordinates that fall within the room excluding the
    walls.

    Parameters
    ----------
    room_top_left: tuple, (x, y)
        The top left coordinates of a room, as used to add that room with
        methods such as `add_room`.
    room_width: int
        The width of the room.
    room_height: int
        The height of the room.

    Returns
    -------
    list, [(x,y), ...]
        A list of (x, y) coordinates that are encapsulated in the
        rectangle, excluding walls.

    See Also
    --------
    WorldBuilder.add_room

    """
    xs = list(range(room_top_left[0] + 1,
                    room_top_left[0] + room_width - 1))
    ys = list(range(room_top_left[1] + 1,
                    room_top_left[1] + room_height -1))
    locs = list(itertools.product(xs, ys))
    return locs


def _flatten_dict(dict_):
    new_dict = {}
    for k, v in dict_.items():
        if isinstance(v, dict):
            sub_dict_ = {f"{k}_{k2}": v2 for k2, v2 in v.items()}
            new_dict = {**new_dict, **sub_dict_}
        else:
            new_dict[k] = v

    return new_dict
