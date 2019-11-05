import threading
import time

from flask import Flask, jsonify, abort
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
app.config['TESTING'] = True
CORS(app)

# variables to be set by MATRXS
# states is a list of length 'current_tick' with a dictionary containing all states of that tick, indexed by agent_id
states = []
current_tick = 0
tick_duration = 0.0
grid_size = [1,1]

# a temporary state for the current tick, which will be written to states after all
# agents have been updated
temp_state = []

# variables to be read (only!) by MATRXS and set (only!) through API calls
userinput = {}



#########################################################################
# API connection methods
#########################################################################



@app.route('/get_info', methods=['GET', 'POST'])
def get_info():
    print(f"Returning tick {current_tick}")
    return jsonify({"tick": current_tick, "tick_duration": tick_duration, "grid_size": grid_size})

@app.route('/get_states/<tick>', methods=['GET', 'POST'])
def get_states(tick):
    """
    Returns the states of all agents and the god view from tick 'tick' onwards.
    :param tick: integer indicating from which tick onwards to send the states.
    :return: States from tick 'tick' onwards of all agents.
    """
    # check for validity and return an error if not valid
    API_call_valid, error = check_API_request(tick)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    print(f"Sending states from tick {tick} onwards")
    return jsonify(fetch_states(tick))


@app.route('/get_states/<tick>/<agent_ids>', methods=['GET', 'POST'])
def get_states_specific_agents(tick, agent_ids):
    """
    Returns the states starting from tick 'tick' for agent 'agent_id'.
    :param tick: integer indicating from which tick onwards to send the states.
    :param agent_ids: integer for indicating a specific agent_id, or a list of agent_ids for returning the states of
    multiple agents
    :return: States from tick 'tick' onwards for agent_ids 'agent_ids'
    """
    # check for validity and return an error if not valid
    API_call_valid, error = check_API_request(tick)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    print(f"Sending states from tick {tick} onwards for agents IDs {agent_ids}")
    return jsonify(fetch_states(tick, agent_ids))


@app.route('/get_latest_state/<agent_ids>', methods=['GET', 'POST'])
def get_god_state(agent_ids):
    """
    Returns the latest states for agents 'agent_ids'
    :param tick: integer indicating from which tick onwards to send the states.
    :return: States from tick 'tick' onwards for the god view
    """

    a = time.time()
    # check for validity and return an error if not valid
    API_call_valid, error = check_API_request(current_tick, agent_ids, ids_required=True)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    return jsonify(fetch_states(current_tick, agent_ids))



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
    """
    Checks if the API request is in valid format, and the targeted values exist
    :param tick: MATRXS tick
    :param ids: string with 1 agent ID, or list of agent IDS
    :return: Success (Boolean indicating whether it is valid or not), Error (if any, prodiving the type and a message)
    See for the error codes https://www.ibm.com/support/knowledgecenter/SS42VS_7.3.0/com.ibm.qradar.doc/c_rest_api_errors.html
    """
    # check if tick is a valid format
    # if not isinstance(tick, int):
    try:
        tick = int(tick)
    except:
        return False, {'error_code': 400, 'error_message': f'Tick has to be an integer, but is of type {type(tick)}'}

    # check if the tick has actually occured
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
                                                    f'does not exist.'}

    # all checks cleared, so return with success and no error message
    return True, None

def fetch_states(tick, ids=None):
    """
    This function filters the states desired by the user, as specified by the tick and (agent)ids.
    :param tick: Tick from which onwards to return the states. Thus will return [tick:current_tick]
    :param ids: Id(s) from agents/god for which to return the states. Can be a string (1 id, e.g. 'god'), or a list of
    strings.
    :return: Returns the filtered states from tick 'tick' onwards to 'current_tick', containing the states for the agents
    as specified in 'ids'.
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
    """
    Creates an error code with a custom message
    """
    response = jsonify({'message': message})
    response.status_code = code
    return response



def __reorder_state(state):
    """
    Convert the state, which is a dictionary of objects with object ID as key,
    into a new dictionary with as key the visualization depth, and as value
    the objects which are to be displayed at that depth
    :param state: The world state, a dictionary with object IDs as keys
    :return sorted_state: The world state, but sorted on visualization depth
    """
    new_state = {}

    # loop through all objects in the state
    for objID, obj in state.items():

        if objID is "World":
            continue

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
    """
    Saves the state of an agent for use via the API
    :param agent_id: ID of the agent of who the state is
    :param state: state of the agent
    :param agent_inheritence_chain: inheritance_chain of classes, can be used
    to figure out type of agent
    """
    temp_state[agent_id] = {'state': __reorder_state(state),
                                          "tick": current_tick,
                                          'agent_inheritence_chain': agent_inheritence_chain}

    # print("States saved:", len(states), "last item:", states[-1])


#########################################################################
# API Flask methods
#########################################################################

def flask_thread():
    """
    Starts the Flask server on localhost:3001
    """
    app.run(host='127.0.0.1', port=3001, debug=False, use_reloader=False)

def run_api():
    """
    Creates a seperate Python thread in which the API (Flask) is started
    :return: MATRXS API Python thread
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
