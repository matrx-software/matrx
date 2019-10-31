import threading
from gevent import sleep

from flask import Flask, render_template, jsonify, abort
from flask_socketio import SocketIO

'''
This file holds the code for the MATRXS RESTful API. 
External scripts can send POST and/or GET requests to retrieve state, tick and other information, and send 
userinput or other information to MATRXS. The API is a Flask (Python) webserver.

For visualization, see the seperate MATRXS visualization folder / package.
'''

debug = True
runs = True  # TODO : bool to stop the API during runtime

app = Flask(__name__, template_folder='static/templates')
# app = None
# io_socket = None
async_mode = "gevent"  # gevent (preferred) or eventlet.

# variables to be read and set by MATRXS
# states is a list of length 'current_tick' with a dictionary containing all states of that tick, indexed by agent_id
states = []
current_tick = 0

userinput = {}



#########################################################################
# API connection methods
#########################################################################

@app.route('/get_tick', methods=['GET', 'POST'])
def get_tick():
    print(f"Returning tick {current_tick}")
    return jsonify(current_tick)

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


@app.route('/get_god_state/<tick>', methods=['GET', 'POST'])
def get_god_state(tick):
    """
    Returns the god states starting from tick 'tick'
    :param tick: integer indicating from which tick onwards to send the states.
    :return: States from tick 'tick' onwards for the god view
    """
    # check for validity and return an error if not valid
    API_call_valid, error = check_API_request(tick)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    print(f"Sending states from tick {tick} onwards for the god view")
    return jsonify(fetch_states(tick))



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
    if not tick in range(0, current_tick):
        return False, {'error_code': 400, 'error_message': f'Indicated tick does not exist, has to be in range 0 - {current_tick}, but is {tick}'}

    # if this API call requires ids, check this variable on validity as well
    if ids_required:

        # check if ids variable is of a valid type
        if not isinstance(ids, str):
            try:
                ids = eval(ids)
            except:
                return False, {'error_code': 400, 'error_message': f'Provided IDs are not of valid format. Provides IDs is of '
                                                                   f'type {type(ids)} but should be either of type string for '
                                                                   f'requesting states of 1 agent (e.g. "god"), or a list of '
                                                                   f'IDs(string) for requesting states of multiple agents'}

        # check if the provided ids exist for all requested ticks
        ids = [ids] if isinstance(ids, str) else ids
        for t in range(tick, current_tick):
            for id in ids:
                if id not in states[t]:
                    return False, {'error_code': 400,
                                   'error_message': f'Trying to fetch the state for agent with ID {id} for tick {t}, but '
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
    for t in range(tick, current_tick):
        states_this_tick = {}

        # add each agent's state for this tick
        for id in ids:
            states_this_tick[id] = states[t][id]

        # save the states of all filtered agents for this tick
        filtered_states.append(states_this_tick)

    return filtered_states


def create_error_response(code, message):
    response = jsonify({'message': message})
    response.status_code = code
    return response


#########################################################################
# API Flask methods
#########################################################################

def flask_thread():
    """
    Starts the Flask server on localhost:3000
    """
    app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False)

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



# def do_stuff():
#     while True:
#         print("API running in bg thread")
#         sleep(1)



#
# @app.route('/update_states', methods=['POST'])
# def update_states():
#     pass
#
# @app.route('/settings/tick_duration')
# def set_tick_duration():
#     pass
#
#
# @app.route('/human-agent/<id>')
# def human_agent_view(id):
#     """
#     Route for HumanAgentBrain
#
#     Parameters
#     ----------
#     id
#         The human agent ID. Is obtained from the URL.
#
#     Returns
#     -------
#     str
#         The template for this agent's view.
#
#     """
#     return render_template('human_agent.html', id=id)
#
#
# # route for agent, get the ID from the URL
# @app.route('/agent/<id>')
# def agent_view(id):
#     """
#     Route for AgentBrain
#
#     Parameters
#     ----------
#     id
#         The agent ID. Is obtained from the URL.
#
#     Returns
#     -------
#     str
#         The template for this agent's view.
#
#     """
#     return render_template('agent.html', id=id)
#
#
# @app.route('/god')
# def god_view():
#     """
#     Route for the 'god' view which contains the ground truth of the world without restrictions.
#
#     Returns
#     -------
#     str
#         The template for this view.
#
#     """
#     return render_template('god.html')
#
#
# @app.route('/avatars')
# # route for agent picture
# def image():
#     """
#     Rout for the images for agents.
#
#     Returns
#     -------
#     str
#         The image template.
#
#     """
#     return render_template('avatars.html')
