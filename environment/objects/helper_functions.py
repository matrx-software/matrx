
object_counter = 0


def next_obj_id():
    global object_counter
    res = object_counter
    object_counter += 1
    return res
