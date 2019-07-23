
object_counter = 0


def next_obj_id():
    global object_counter
    res = object_counter
    object_counter += 1
    return res


def get_inheritence_path(callable_class):
    parents = callable_class.mro()
    parents = [str(p.__name__) for p in parents]
    return parents
