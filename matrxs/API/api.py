import threading
import time
import copy
import warnings

from flask import Flask, jsonify, abort, request
from flask_cors import CORS

'''
This file holds the code for the MATRXS RESTful API.
External scripts can send POST and/or GET requests to retrieve state, tick and other information, and send
userinput or other information to MATRXS. The API is a Flask (Python) webserver.

For visualization, see the seperate MATRXS visualization folder / package.
'''

debug = True
runs = True  # TODO : bool to stop the API during runtime

app = Flask(__name__)
CORS(app)

# variables to be set by MATRXS
# states is a list of length 'current_tick' with a dictionary containing all states of that tick, indexed by agent_id
states = []
current_tick = 0
tick_duration = 0.0
grid_size = [1, 1]
MATRXS_info = {}
next_tick_info = {}


# a temporary state for the current tick, which will be written to states after all
# agents have been updated
temp_state = []

# variables to be read (only!) by MATRXS and set (only!) through API calls
userinput = {}
matrxs_paused = False
matrxs_done = False
tick_duration = 0.5

#########################################################################
# API connection methods
#########################################################################



@app.route('/get_info', methods=['GET', 'POST'])
def get_info():
    """ Provides the general information on the world, contained in the world object.

    Returns
        MATRXS world object, contianing general information on the world and scenario.
    -------
    """
    print(f"Returning tick {current_tick}")
    # return jsonify({"tick": current_tick, "tick_duration": tick_duration, "grid_size": grid_size})
    return jsonify(MATRXS_info)

@app.route('/get_states/<tick>', methods=['GET', 'POST'])
def get_states(tick):
    """ Provides the states of all agents (including the god view) from tick 'tick' onwards to current tick.

    Parameters
    ----------
    tick
        integer indicating from which tick onwards to send the states.
    Returns
        Returns a list of length 'tick' to current_tick. For each tick (item in the list), a dictionary contains the
        state for each agent existing in the simulation, indexed by their agent ID.
    -------
    """

    # check for validity and return an error if not valid
    API_call_valid, error = check_API_request(tick)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    print(f"Sending states from tick {tick} onwards")
    return jsonify(__fetch_states(tick))


@app.route('/get_states/<tick>/<agent_ids>', methods=['GET', 'POST'])
def get_states_specific_agents(tick, agent_ids):
    """ Provides the states starting from tick 'tick' to current_tick, for the agents specified in 'agent_ids'.

    Parameters
    ----------
    tick
        integer indicating from which tick onwards to send the states.
    agent_ids
        One agent ID, or a List of agent IDs for which the states should be returned. God view = "god"

    Returns
        Returns a list of length 'tick' to current_tick. For each tick (item in the list), a dictionary contains the
        state for each agent as specified in 'agent_ids', indexed by their agent ID.
    -------
    """
    # check for validity and return an error if not valid
    API_call_valid, error = check_API_request(tick)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    print(f"Sending states from tick {tick} onwards for agents IDs {agent_ids}")
    return jsonify(__fetch_states(tick, agent_ids))


@app.route('/get_latest_state/<agent_ids>', methods=['GET', 'POST'])
def get_latest_state(agent_ids):
    """ Provides the latest state of one or multiple agents

    Parameters
    ----------
    agent_ids
        IDs of agents for which to send the latest state. Either a single agent ID, or a list of agent IDs.
        God view = "god"

    Returns
        Returns a list of length 'tick' to current_tick. For each tick, a dictionary contains the states for each
        agent as specified in 'agent_ids', indexed by their agent ID.
    -------
    """

    a = time.time()
    # check for validity and return an error if not valid
    API_call_valid, error = check_API_request(current_tick, agent_ids, ids_required=True)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    return jsonify(__fetch_states(current_tick, agent_ids))


@app.route('/send_userinput/<agent_ids>', methods=['GET', 'POST'])
def send_userinput(agent_ids):
    """ Can be used to send user input from the user (pressed keys) to the specified human agent(s) in MATRXS

    Parameters
    ----------
    agent_ids
        ID(s) of the human agent(s) to which the data should be passed.

    Returns
        returns True if the data was valid (right now always)
    -------

    """
    global userinput

    API_call_valid, error = check_API_request(current_tick, agent_ids, ids_required=True)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    # make sure the ids are a list
    try:
        agent_ids = eval(agent_ids)
    except:
        agent_ids = [agent_ids]

    # fetch the data from the request object
    data = request.json

    # add each pressed key as userinput for each specified human agent
    for agent_id in agent_ids:
        for pressed_key in data:

            # add  the agent_id if not existing yet
            if agent_id not in userinput:
                userinput[agent_id] = []

            # save the pressed key of the agent
            userinput[agent_id].append(pressed_key)
            # try:
            #
            #     userinput[agent_id].append(pressed_key)
            #
            # except:
            #     warnings.warn("API userinputs list was emptied while adding user input, skipping")

    return jsonify(True)


def send_message(agent_ids):
    pass



@app.route('/pause', methods=['GET', 'POST'])
def pause_MATRXS():
    """ Pause the MATRXS simulation

    Returns
        True if paused, False if already paused
    -------
    """
    global matrxs_paused
    if not matrxs_paused:
        matrxs_paused = True
        return jsonify(True)
    else:
        return jsonify(False)

@app.route('/start', methods=['GET', 'POST'])
def start_MATRXS():
    """ Starts / unpauses the MATRXS simulation

    Returns
        True if it has been started, False if it is already running
    -------

    """
    global matrxs_paused
    if matrxs_paused:
        matrxs_paused = False
        return jsonify(True)
    else:
        return jsonify(False)

@app.route('/stop', methods=['GET', 'POST'])
def stop_MATRXS():
    """ Stops MATRXS scenario

    Returns
        True
    -------
    """
    global matrxs_done
    matrxs_done = True
    return jsonify(True)

@app.route('/change_tick_duration/<tick_dur>', methods=['GET', 'POST'])
def change_MATRXS_speed(tick_dur):
    """ Change the tick duration / simulation speed of MATRXS

    Parameters
    ----------
    tick_duration
        The duration of 1 tick

    Returns
        True if successfully changed tick speed (400 error if tick_duration not valid)
    -------
    """
    # check if the passed value is a float / int, and return an error if not
    try:
        float(tick_dur)
    except:
        return abort(400, description=f'Tick duration has to be an float, but is of type {type(tick_dur)}')

    # save the new tick duration
    global tick_duration
    tick_duration = float(tick_dur)
    return jsonify(True)

#########################################################################
# Errors
#########################################################################

@app.errorhandler(400)
def bad_request(e):
    print("Throwing error", e)
    return jsonify(error=str(e)), 400


#########################################################################
# API helper methods
#########################################################################

def check_API_request(tick=None, ids=None, ids_required=False):
    """ Checks if the variables of the API request are valid, and if the requested information exists

    Parameters
    ----------
    tick
        MATRXS tick
    ids
        string with 1 agent ID, or list of agent IDS
    ids_required
        Whether IDS are required
    Returns
        Success (Boolean indicating whether it is valid or not), Error (if any, prodiving the type and a message)
        See for the error codes https://www.ibm.com/support/knowledgecenter/SS42VS_7.3.0/com.ibm.qradar.doc/c_rest_api_errors.html
    -------

    """
    # check if tick is a valid format
    # if not isinstance(tick, int):
    try:
        tick = int(tick)
    except:
        return False, {'error_code': 400, 'error_message': f'Tick has to be an integer, but is of type {type(tick)}'}

    # check if the tick has actually occurred
    if not tick in range(0, current_tick+1):
        return False, {'error_code': 400, 'error_message': f'Indicated tick does not exist, has to be in range 0 - {current_tick}, but is {tick}'}

    # if this API call requires ids, check this variable on validity as well
    if ids_required:

        # check if ids variable is of a valid type
        try:
            ids = eval(ids)
        except:
            pass
            # return False, {'error_code': 400, 'error_message': f'Provided IDs are not of valid format. Provides IDs is of '
            #                                                    f'type {type(ids)} but should be either of type string for '
            #                                                        f'requesting states of 1 agent (e.g. "god"), or a list of '
            #                                                        f'IDs(string) for requesting states of multiple agents'}

        # check if the provided ids exist for all requested ticks
        ids = [ids] if isinstance(ids, str) else ids
        for t in range(tick, current_tick+1):
            for id in ids:
                if id not in states[t]:
                    return False, {'error_code': 400,
                                   'error_message': f'Trying to fetch the state for agent with ID "{id}" for tick {t}, but '
                                                    f'no data on that agent exists for that tick. Is the agent ID correct?'}

    # all checks cleared, so return with success and no error message
    return True, None

def __fetch_states(tick, ids=None):
    """ This private function fetches, filters and orders the states as specified by the tick and agent ids.
    
    Parameters
    ----------
    tick
        Tick from which onwards to return the states. Thus will return a list of length [tick:current_tick]
    ids
        Id(s) from agents/god for which to return the states. Either a single agent ID or a list of agent IDs.
        God view = "god"
    Returns
        Returns a list of length [tick:current_tick]. For each tick, a dictionary contains the states for each agent as
        specified in 'agent_ids', indexed by their agent ID.
    -------
    """
    tick = int(tick)

    # return all states
    if ids is None:
        return states[tick:]

    # convert ints to lists so we can use 1 uniform approach
    try:
        ids = eval(ids)
    except:
        ids = [ids]

    # create a list containing the states from tick to current_tick containing the states of all desired agents/god
    filtered_states = []
    for t in range(tick, current_tick+1):
        states_this_tick = {}

        # add each agent's state for this tick
        for id in ids:
            states_this_tick[id] = states[t][id]

        # save the states of all filtered agents for this tick
        filtered_states.append(states_this_tick)

    return filtered_states


def create_error_response(code, message):
    """ Creates an error code with a custom message """
    response = jsonify({'message': message})
    response.status_code = code
    return response



def __reorder_state(state):
    """ This private function converts the MATRXS state from indexing based on object ID, to indexing based on visualization
    depth.

    Parameters
    ----------
    state
         The world state, a dictionary with object IDs as keys
    Returns
        The world state, but sorted on visualization depth
    -------
    """
    new_state = {}

    # loop through all objects in the state
    for objID, obj in state.items():

        # add the World object at depth 0, and the others at their own respective visualization depth
        vis_depth = 0
        if not objID is "World":
            # fetch the visualization depth
            vis_depth = state[objID]["visualization"]['depth']

            if "sense_capability" in obj:
                obj["sense_capability"] = str(obj["sense_capability"])


        # save the object in the new_state dict at its visualization_depth
        if vis_depth not in new_state:
            new_state[vis_depth] = {}

        # add the object or agent to the list at the (x,y) location in the dict
        new_state[vis_depth][objID] = obj

    # sort dict on depth
    sorted_state = {}
    for depth in sorted(new_state.keys()):
        sorted_state[depth] = new_state[depth]

    return sorted_state


def add_state(agent_id, state, agent_inheritence_chain):
    """ aves the state of an agent for use via the API

    Parameters
    ----------
    agent_id
         ID of the agent of who the state is
    state
        state as filtered by the agent
    agent_inheritence_chain
         inheritance_chain of classes, can be used to figure out type of agent
    -------
    """
    # save the new general info on the MATRXS World (once)
    global next_tick_info
    if next_tick_info == {}:
        next_tick_info = state["World"]

    # reorder and save the new state along with some meta information
    temp_state[agent_id] = {'state': __reorder_state(state),
                                          "tick": current_tick,
                                          'agent_inheritence_chain': agent_inheritence_chain}



def next_tick():
    """ Proceed to the next tick, publicizing data of the new tick via the API (the new states).
    -------
    """
    # save the new general info
    global MATRXS_info, next_tick_info
    MATRXS_info = copy.copy(next_tick_info)
    next_tick_info = {}

    # publicize the states of the previous tick
    states.append(copy.copy(temp_state))

# def pop_received_data(agent_id):
#     """ Pop the user input for an agent from the received_data dictionary and return it
#
#     Parameters
#     ----------
#     agent_id
#         ID of the agent for which to return the received input
#
#     Returns
#         A dictionary containing the type of input (e.g. "pressed_keys" or "chat_messages"), and their value (or a list
#         of values if multiple inputs of the same type were received within 1 tick). See the `send_data()` function for
#         more information.
#     -------
#     """
#     global received_data
#     return received_data.pop(agent_id, None)

def pop_userinput(agent_id):
    """ Pop the user input for an agent from the userinput dictionary and return it

    Parameters
    ----------
    agent_id
        ID of the agent for which to return the userinput

    Returns
        A list of keys pressed. See this link for the encoding of keys: https://developer.mozilla.org/nl/docs/Web/API/KeyboardEvent/key/Key_Values
    -------
    """
    global userinput
    return userinput.pop(agent_id, None)


def reset_api():
    """ Reset the api MATRXS variables """
    global temp_state, userinput, matrxs_paused, matrxs_done
    temp_state = []
    userinput = {}
    matrxs_paused = False
    matrxs_done = False

#########################################################################
# API Flask methods
#########################################################################

def flask_thread():
    """ Starts the Flask server on localhost:3001
    -------
    """
    app.run(host='0.0.0.0', port=3001, debug=False, use_reloader=False)

def run_api():
    """ Creates a seperate Python thread in which the API (Flask) is started
    Returns
        MATRXS API Python thread
    -------
    """
    print("Starting background API server")
    global runs
    runs = True

    print("Initialized app:", app)
    API_thread = threading.Thread(target=flask_thread)
    API_thread.start()
    return API_thread

if __name__ == "__main__":
    run_api()