import math


def get_all_classes(class_, omit_super_class=False):

    # Include given class or not
    if omit_super_class:
        subclasses = set()
    else:
        subclasses = set([class_])

    # Go through all child classes
    work = [class_]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)

    # Create a dict out of it
    act_dict = {}
    for action_class in subclasses:
        act_dict[action_class.__name__] = action_class

    return act_dict


def get_all_inherited_classes(super_type):
    all_classes = {super_type}
    work = [super_type]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in all_classes:
                all_classes.add(child)
                work.append(child)

    class_dict = {}
    for classes in all_classes:
        class_dict[classes.__name__] = classes

    return class_dict


def get_distance(coord1, coord2):
    """ Get distance between two x,y coordinates """
    dist = [(a - b) ** 2 for a, b in zip(coord1, coord2)]
    dist = math.sqrt(sum(dist))
    return dist