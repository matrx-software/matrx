import threading
import time
import copy
import logging

from flask import Flask, jsonify, abort, request
from flask_cors import CORS

from matrxs.utils.message import Message

'''
This file holds the code for the MATRXS RESTful API.
External scripts can send POST and/or GET requests to retrieve state, tick and other information, and send
userinput or other information to MATRXS. The API is a Flask (Python) webserver.

For visualization, see the seperate MATRXS visualization folder / package.
'''

debug = True

app = Flask(__name__)
CORS(app)
port = 3001

# variables to be set by MATRXS
# states is a list of length 'current_tick' with a dictionary containing all states of that tick, indexed by agent_id
states = []
current_tick = 0
tick_duration = 0.0
grid_size = [1, 1]
MATRXS_info = {}
next_tick_info = {}
add_message_to_agent = None
received_messages = {} # messages received via the API, intended for the Gridworld
gw_message_manager = None # the message manager of the gridworld, containing all messages of various types
teams = None # dict with team names (keys) and IDs of agents who are in that team (values)
# currently only one world at a time is supported
current_world_ID = False

# a temporary state for the current tick, which will be written to states after all
# agents have been updated
temp_state = {}

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
        MATRXS world object, containing general information on the world and scenario.
    -------
    """
    MATRXS_info['matrxs_paused'] = matrxs_paused
    return jsonify(MATRXS_info)


@app.route('/get_latest_state_and_messages/<agent_id>', methods=['GET', 'POST'])
def get_latest_state_and_messages(agent_id):
    """ Provides both the state and messages from the latest tick for one particular agent

    Parameters
    ----------
    agent_id
        The ID of the targeted agent
    Returns
        a dictionary containing the states under the "states" key, and the messages under the "messages" key.
    -------

    """
    # check for validity and return an error if not valid
    API_call_valid, error = check_states_API_request(ids=[agent_id])
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    # fetch states and messages
    states = __fetch_states(current_tick, agent_id)
    messages = __fetch_messages(current_tick, agent_id)

    return jsonify({"states": states, "messages": messages})

#########################################################################
# MATRX fetch state API calls
#########################################################################

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
    API_call_valid, error = check_states_API_request(tick=tick)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

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
    API_call_valid, error = check_states_API_request(tick=tick)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

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
    return get_states_specific_agents(current_tick, agent_ids)



#########################################################################
# MATRX fetch messages API calls
#########################################################################
@app.route('/get_states/<tick>', methods=['GET', 'POST'])
def get_messages(tick):
    """ Provides the messages of all agents from tick 'tick' onwards to current tick.

    Parameters
    ----------
    tick
        integer indicating from which tick onwards to send the messages.
    Returns
        Returns a list of length 'tick' to current_tick. For each tick (item in the list), a dictionary contains ...
    -------
    """

    # check for validity and return an error if not valid
    API_call_valid, error = check_messages_API_request(tick=tick)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    print(f"Sending states from tick {tick} onwards")
    return jsonify(__fetch_messages(tick))



@app.route('/get_messages/<tick>/<agent_id>', methods=['GET', 'POST'])
def get_messages_specific_agent(tick, agent_id):
    """ Provides all messages either send by or addressed to 'agent_id', from tick 'tick' onwards.

    Parameters
    ----------
    tick
    agent_ids

    Returns
    -------

    """
    # check for validity and return an error if not valid
    API_call_valid, error = check_messages_API_request(tick=current_tick, id=agent_id)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    messages = __fetch_messages(tick, agent_id)

    return jsonify(messages)

@app.route('/get_latest_messages', methods=['GET', 'POST'])
def get_latest_messages():
    """ Provides all messages of the latest tick.

    Parameters
    ----------
    agent_id

    Returns
    -------

    """
    # check for validity and return an error if not valid
    API_call_valid, error = check_messages_API_request(tick=current_tick)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    messages = __fetch_messages(current_tick)

    return jsonify(messages)

@app.route('/get_latest_messages/<agent_id>', methods=['GET', 'POST'])
def get_latest_messages_specific_agent(agent_id):
    """ Provides the messages of the latest tick either sent by or addressed to 'agent_id'.

    Parameters
    ----------
    agent_id

    Returns
    -------

    """
    # check for validity and return an error if not valid
    API_call_valid, error = check_messages_API_request(tick=current_tick, id=agent_id)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    messages = __fetch_messages(current_tick, agent_id)

    return jsonify(messages)


#########################################################################
# MATRX userinput API calls
#########################################################################

@app.route('/send_userinput/<agent_ids>', methods=['POST'])
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

    API_call_valid, error = check_states_API_request(current_tick, agent_ids, ids_required=True)
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

    return jsonify(True)

@app.route('/send_message', methods=['POST'])
def send_message():
    """ Send a message containing information to one or multiple specific agent, the agent's team, or all agents

    Message as defined in matrx.utils.message

    Parameters
    ----------
    message
        Message contents to send
    sender
        ID of (human)agent from which sent the message
    receiver
        ID(s) (human)agents which will receive the message. Multiple options available:
        ID or list of agent IDs (JS/Python) =   send to specific agent(s)
        null (JS)       = None (Python)     =   send to all agents
        teamname (JS / Python)              =   send to everyone in the team

    Returns
    -------
        Error if API call invalid, or True if valid.
    """
    # fetch the data
    data = request.json

    # check validity of agent IDs
    API_call_valid, error = check_states_API_request(current_tick, data['receiver'] + data['sender'], ids_required=True)
    if not API_call_valid:
        print("API request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    # create message
    msg = Message(content=data['message'], from_id=data['sender'], to_id=data['receiver'])

    print("API: Receiver of message:", data['receiver'])

    # add the received_messages to the API global variable
    if data['sender'] not in received_messages:
        received_messages[data['sender']] = []
    received_messages[data['sender']].append(msg)

    return jsonify(True)


#########################################################################
# MATRX control API calls
#########################################################################


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


@app.route('/shutdown_API', methods=['GET', 'POST'])
def shutdown():
    """ Shuts down the API by stopping the Flask thread

    Returns
        True
    -------
    """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Unable to shutdown API server. Not running with the Werkzeug Server')
    func()
    print("API server shutting down...")
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



def check_messages_API_request(tick=None, id=None):
    """ Checks if the variables of the API request are valid, and if the requested information exists

    Parameters
    ----------
    tick
    id

    Returns
    -------

    """
    tick = current_tick if tick is None else tick
    # check user input, such as tick
    check_passed, error_message = check_input(tick)
    if not check_passed:
        return False, error_message




    return True, None


def check_states_API_request(tick=None, ids=None, ids_required=False):
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
    # check user input, such as tick and agent id
    check_passed, error_message = check_input(tick)
    if not check_passed:
        return False, error_message

    # Don't throw an error if MATRXS is paused the first tick, and thus still has no states
    # if current_tick is 0 and matrxs_paused:
    #     return True, None

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

        # check if the API was reset during this time
        if len(states) is 0:
            return False, {'error_code': 400,
                           'error_message': f'API is reconnecting to a new world'}

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


def check_input(tick=None, ids=None):

    # check if tick is a valid format
    if tick is not None:
        try:
            tick = int(tick)
        except:
            return False, {'error_code': 400,
                           'error_message': f'Tick has to be an integer, but is of type {type(tick)}'}

        # check if the tick has actually occurred
        if not tick in range(0, current_tick + 1):
            return False, {'error_code': 400,
                           'error_message': f'Indicated tick does not exist, has to be in range 0 - {current_tick}, but is {tick}'}

    return True, None


def __fetch_messages(tick, id=None):
    """ Fetch the messages from the GridWorld MessageManager, as requested via the API call.
    Messages to be fetched can be filtered by start tick and the agent id.

    Parameters
    ----------
    tick
        All messages from this tick onwards to the current_tick will be collected.
    id
        Only messages received by or sent by this agent will be collected.

    Returns
    -------
    Dictionary containing a 'global', 'team', and 'private' subdictionary. These subdictionaries contain a list of
    all messages, indexed by tick number.

    """
    messages = {'global': {}, 'team': {}, 'private': {}}

    # loop through all requested ticks
    for t in range(tick, current_tick + 1):
        # initialize the message objects to return
        messages['global'][tick] = None
        messages['team'][tick] = None
        messages['private'][tick] = None

        # fetch any existing global messages for this tick
        if tick in gw_message_manager.global_messages:
            # make the messages JSON serializable and add
            messages['global'][tick] = [mssg.toJSON() for mssg in gw_message_manager.global_messages[tick]]

        # fetch any team messages
        if tick in gw_message_manager.team_messages:
            # fetch all team messages
            if id is None:
                # make them JSON serializable
                messages['team'][tick] = [mssg.toJSON() for mssg in gw_message_manager.team_messages[tick]]

            # fetch team messages of the team of which the agent is a member
            else:
                for team in teams:
                    if id in team and team in gw_message_manager.team_messages[tick]:
                        # make the messages JSON serializable and add
                        messages['team'][tick] = [mssg.toJSON() for mssg in gw_message_manager.team_messages[tick][team]]


        # fetch private messages
        if tick in gw_message_manager.private_messages:
            # fetch all private messages
            if id is None:
                # make the messages JSON serializable and add
                messages['private'][tick] = [mssg.toJSON() for mssg in gw_message_manager.private_messages[tick]]

            # fetch private messages sent to or received by the specified agent
            else:
                messages['private'][tick] = []
                for message in gw_message_manager.private_messages[tick]:
                    # only private messages addressed to or sent by our agent are requested
                    if message.from_id == id or message.to_id == id:
                        # make the messages JSON serializable and add
                        messages['private'][tick].append(message.toJSON())

    return messages

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
    """ This private function makes the MATRXS state ready for sending as a JSON object

    Parameters
    ----------
    state
         The world state, a dictionary with object IDs as keys
    Returns
        The world state, JSON serializable
    -------
    """
    new_state = copy.copy(state)

    # loop through all objects in the state
    for objID, obj in state.items():

        if not objID is "World":
            # make the sense capability JSON serializable
            if "sense_capability" in obj:
                new_state[objID]["sense_capability"] = str(obj["sense_capability"])

    return new_state


def add_state(agent_id, state, agent_inheritence_chain, world_settings):
    """ aves the state of an agent for use via the API

    Parameters
    ----------
    agent_id
         ID of the agent of who the state is
    state
        state as filtered by the agent
    agent_inheritence_chain
         inheritance_chain of classes, can be used to figure out type of agent
    world_settings
        This object contains all information on the MATRXS world, such as tick and grid_size. Some agents might filter
        these out of their state, as such it is sent along seperatly to make sure the world settings, required by the
        visualization, are passed along.
    -------
    """
    # save the new general info on the MATRXS World (once)
    global next_tick_info
    if next_tick_info == {}:
        next_tick_info = world_settings

    # Make sure the world settings are in the state, as these are used by the visualization
    if 'World' not in state:
        state['World'] = world_settings

    state['World']['matrxs_paused'] = matrxs_paused

    # reorder and save the new state along with some meta information
    temp_state[agent_id] = {'state': __reorder_state(state), 'agent_inheritence_chain': agent_inheritence_chain}



def next_tick():
    """ Proceed to the next tick, publicizing data of the new tick via the API (the new states).
    -------
    """
    # save the new general info
    global MATRXS_info, next_tick_info
    MATRXS_info = copy.copy(next_tick_info)
    next_tick_info = {}
    # print("Next ticK:", MATRXS_info);

    # publicize the states of the previous tick
    states.append(copy.copy(temp_state))


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
    """ Reset the MATRXS API variables """
    global temp_state, userinput, matrxs_paused, matrxs_done, states, current_tick, tick_duration, grid_size
    global MATRXS_info, next_tick_info, received_messages, current_world_ID
    temp_state = {}
    userinput = {}
    matrxs_paused = False
    matrxs_done = False
    states = []
    current_tick = 0
    tick_duration = 0.0
    grid_size = [1, 1]
    MATRXS_info = {}
    next_tick_info = {}
    received_messages = {}
    current_world_ID = False



def register_world(world_ID):
    """ Register a new simulation world

    At the moment simulation of only one world at a time is supported, so this calling this function will discard
    the previous world.

    Parameters
    ----------
    world_ID
        The ID of the world
    -------
    """
    global current_world_ID
    current_world_ID = world_ID


#########################################################################
# API Flask methods
#########################################################################

def flask_thread():
    """ Starts the Flask server on localhost:3001
    -------
    """
    if not debug:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


def run_api(verbose):
    """ Creates a seperate Python thread in which the API (Flask) is started
    Returns
        MATRXS API Python thread
    -------
    """
    print("Starting background API server")
    global debug
    debug = verbose

    print("Initialized app:", app)
    API_thread = threading.Thread(target=flask_thread)
    API_thread.start()
    return API_thread

if __name__ == "__main__":
    run_api()
