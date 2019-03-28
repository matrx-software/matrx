import datetime
import requests

def reorder_state_for_GUI(state):
    """
    Reorder the state such that it has the x,y coords as keys and can be JSON serialized
    Old state order: { 'object_name' : {obj_properties}, 'object_name2' : {obj_properties}, ....}
    New state order: { 'x1_y1') : [obj1, obj2, agent1], 'x2_y1' : [obj3, obj4, agent1], ...}
    :param state: state of all visible objects for that entity
    :return: state reordered
    """
    newState = {}
    for obj in state:

        # convert the [x,y] coords to a x_y notation so we can use it as a key which is
        # also JSON serializable
        strXYkey = str(state[obj]['location'][0]) + "_" + str(state[obj]['location'][1])

        # create a new list with (x,y) as key if it does not exist yet in the newState dict
        if strXYkey not in newState:
            newState[strXYkey] = []

        # add the object or agent to the list at the (x,y) location in the dict
        newState[strXYkey].append( state[obj] )

    return newState



def sendGUIupdate(state, grid_size, type, id=None):
    """
    A function that can be called by the (human)agents or the gridworld, which
    will send an update to the GUI server with an update of the world state
    :param state: state of all visible objects for that entity
    :param grid_size: grid size of the grid in shape [x, y]
    :param type: type of entity, either 'god', 'agent' or 'humanagent'
    :param id (optional): ID of the object
    :return: userinput if type humanagent, otherwise True
    """
    # reorder state so it is can be send to and read more easily by the GUI server
    newState = reorder_state_for_GUI(state)
    # print(f"{type} state reordered: {newState}")

    # if type is 'god':
    #     print(f"Sending update to GUI API for god view")
    # else:
    #     print(f"Sending update to GUI API for {type} with ID: {id}")

    # put data in a json array
    data = {'params': {'grid_size': grid_size}, 'state': newState}

    # construct the update url
    url = 'http://localhost:3000/'
    if type == "agent":
        url += "update/agent/" + id
    elif type == "god":
        url += "update/god"
    elif type == "humanagent":
        url += "update/agent/" + id

    tick_start_time = datetime.datetime.now()

    # send an update of the agent state to the GUI via its API
    r = requests.post(url, json=data)


    tick_end_time = datetime.datetime.now()
    tick_duration = tick_end_time - tick_start_time
    # print("Request + reply took:", tick_duration.total_seconds())
    # print("post url:", r.url)

    # check for errors in the response
    if r.status_code != requests.codes.ok:
        if type is 'god':
            print(f"Error in contacting GUI API for god view")
        else:
            print(f"Error in contacting GUI API for {type} with ID: {id}")
    # else:
    #     print("Request returned ok. Status code:", r.status_code)

    # return userinputs for humanagent
    if type is "humanagent":
        return r.json

    # otherwise return nothing
    return ""
