import threading
import copy
import logging

import jsonpickle
from flask import Flask, jsonify, abort, request
from flask_cors import CORS

from matrx.messages.message import Message

'''
This file holds the code for the MATRX RESTful api.
External scripts can send POST and/or GET requests to retrieve state, tick and other information, and send
userinput or other information to MATRX. The api is a Flask (Python) webserver.

For visualization, see the seperate MATRX visualization folder / package.
'''

debug = True

app = Flask(__name__)
CORS(app)
port = 3001

# variables to be set by MATRX
# states is a list of length 'current_tick' with a dictionary containing all states of that tick, indexed by agent_id
states = {}
current_tick = 0
tick_duration = 0.5
grid_size = [1, 1]
nr_states_to_store = 5
MATRX_info = {}
next_tick_info = {}
add_message_to_agent = None
received_messages = {}  # messages received via the api, intended for the Gridworld
gw_message_manager = None  # the message manager of the gridworld, containing all messages of various types
gw = None
teams = None  # dict with team names (keys) and IDs of agents who are in that team (values)
# currently only one world at a time is supported
current_world_ID = False

# a temporary state for the current tick, which will be written to states after all
# agents have been updated
temp_state = {}

# variables to be read (only!) by MATRX and set (only!) through api calls
userinput = {}
matrx_paused = False
matrx_done = False


#########################################################################
# api connection methods
#########################################################################


@app.route('/get_info', methods=['GET', 'POST'])
def get_info():
    """ Provides the general information on the world, contained in the world object.

    Returns
        MATRX world object, containing general information on the world and scenario.
    -------
    """
    MATRX_info['matrx_paused'] = matrx_paused
    return jsonify(MATRX_info)


@app.route('/get_latest_state_and_messages/', methods=['GET', 'POST'])
def get_latest_state_and_messages():
    """ Provides all most recent information from MATRX for 1 agent: The state from the latest tick, and any new
    messages and chatrooms.

    Parameters should be passed via GET URL parameters.

    A combination of :func:`~matrx.api.api.get_latest_state` and :func:`~matrx.api.api.get_messages`. See those
    two functions for their respective documentation.

    Parameters
    ----------
    agent_id : (required GET URL parameter, default {})
        The ID of the targeted agent. Only the state of that agent, and chatrooms in which that agent is part will be
        sent.

    chat_offsets : (optional GET URL parameter, default {})
        It is not efficient to send every message every tick. With this offsets dict the requestee can
        indicate for every chatroom, which messages they already have, such that only new messages can be sent.
        The `offsets` URL parmaeter should be a dict with as keys the chatroom ID, and as values the message offset.
        The message offset is the index of the message.
        Example of a valid dict: {"0": "10", "3": "5"}.
        This returns the message with index 10+ for the chatroom with ID 0 (global chat),
        and messages with index 5+ for chatroom with ID 3.

    Returns
    -------
        A dictionary containing the states under the "states" key, and the chatrooms with messages under the
         "chatrooms" key.

    """

    # from GET requests fetch URL parameters
    if request.method == "GET":
        error_mssg = f"The /get_latest_state_and_messages/ API call only allows POST requests for MATRX Version 2.0.0 " \
                     f"and higher. Please see https://matrx-software.com/docs/upgrading-matrx on how to upgrade."
        print("api request not valid:", error_mssg)
        return abort(400, description=error_mssg)

    # For POST requests fetch json data
    elif request.method == "POST":
        data = request.json
        agent_id = None if "agent_id" not in data else data['agent_id']
        chat_offsets = None if "chat_offsets" not in data else data['chat_offsets']

    else:
        error_mssg = f"API call only allows POST requests."
        print("api request not valid:", error_mssg)
        return abort(400, description=error_mssg)

    # agent_id is required
    if not isinstance(agent_id, str):
        error_mssg = f"Agent_id passed to /get_latest_state_and_messages API request is not of valid format: " \
                     f"{agent_id}. Should be string."
        print("api request not valid:", error_mssg)
        return abort(400, description=error_mssg)

    # check for validity and return an error if not valid
    api_call_valid, error = check_states_API_request(ids=[agent_id])
    if not api_call_valid:
        print("api request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    # fetch states, chatrooms and messages
    states_ = __fetch_states(current_tick, agent_id)
    chatrooms, messages = get_messages(agent_id, chat_offsets)

    return jsonify({"matrx_paused": matrx_paused, "states": states_, "chatrooms": chatrooms, "messages": messages})


#
# @app.route('/get_latest_state_and_messages/<agent_id>', methods=['GET', 'POST'])
# def get_latest_state_and_messages(agent_id):
#     """ Provides all most recent information from MATRX: Both the state and messages from the latest
#     tick for one particular agent, as well as the current MATRX status (paused or not).
#
#     Parameters
#     ----------
#     agent_id
#         The ID of the targeted agent
#
#     agent_id : (optional GET URL parameter, default None)
#         Agent ID string that will make this function only return chatrooms of which that agent is part. Defaults to
#         None, returning all chatsrooms and all chat messages.
#
#     offsets : (optional GET URL parameter, default {})
#         GET URL parameter that should be a dict with as key the chatroom ID, and as value the message offset. E.g.
#         {"0": "10", "3": "5"}. This returns the message with index 10+ for the chatroom with ID 0 (global chat),
#         and messages with index 5+ for chatroom with ID 3.
#
#     Returns
#     -------
#         a dictionary containing the states under the "states" key, and the messages under the "messages" key.
#
#     """
#     # TODO: deprecated
#     # check for validity and return an error if not valid
#     api_call_valid, error = check_states_API_request(ids=[agent_id])
#     if not api_call_valid:
#         print("api request not valid:", error)
#         return abort(error['error_code'], description=error['error_message'])
#
#     # fetch states and chatrooms with messages
#     states_ = __fetch_states(current_tick, agent_id)
#     chatrooms = get_messages(request)
#
#     return jsonify({"matrx_paused": matrx_paused, "states": states_, "messages": {}, "chatrooms": chatrooms})


#########################################################################
# MATRX fetch state api calls
#########################################################################

@app.route('/get_states/<tick>', methods=['GET', 'POST'])
def get_states(tick):
    """ Provides the states of all agents (including the god view) from tick `tick` onwards to current tick.

    Parameters
    ----------
    tick
        integer indicating from which tick onwards to send the states.

    Returns
    -------
        Returns a list of length `tick` to current_tick. For each tick (item in the list), a dictionary contains the
        state for each agent existing in the simulation, indexed by their agent ID.

    """
    # fetch URL parameters
    agent_id = request.args.get("agent_id")
    chat_offsets = request.args.get("chat_offsets")

    # check for validity and return an error if not valid
    api_call_valid, error = check_states_API_request(tick=tick)
    if not api_call_valid:
        print("api request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    return jsonify(__fetch_states(tick))


@app.route('/get_states/<tick>/<agent_ids>', methods=['GET', 'POST'])
def get_states_specific_agents(tick, agent_ids):
    """ Provides the states starting from tick `tick` to current_tick, for the agents specified in `agent_ids`.

    Parameters
    ----------
    tick
        integer indicating from which tick onwards to send the states.
    agent_ids
        One agent ID, or a List of agent IDs for which the states should be returned. God view = "god"

    Returns
    -------
        Returns a list of length `tick` to current_tick. For each tick (item in the list), a dictionary contains the
        state for each agent as specified in `agent_ids`, indexed by their agent ID.

    """
    # check for validity and return an error if not valid
    api_call_valid, error = check_states_API_request(tick=tick)
    if not api_call_valid:
        print("api request not valid:", error)
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
    -------
        Returns a list of length `tick` to current_tick. For each tick, a dictionary contains the states for each
        agent as specified in `agent_ids`, indexed by their agent ID.

    """
    return get_states_specific_agents(current_tick, agent_ids)


@app.route('/get_filtered_latest_state/<agent_ids>', methods=['POST'])
def get_filtered_latest_state(agent_ids):
    """ Return a state for a set of agent IDs, filtered to only return the specified properties
    """

    # check for validity and return an error if not valid
    api_call_valid, error = check_states_API_request(tick=current_tick)
    if not api_call_valid:
        print("api request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    # Get the agent states
    agent_states = __fetch_states(current_tick, agent_ids)[0]

    # Filter the agent states based on the received properties list
    props = request.json['properties']
    if 'filters' in request.json.keys():
        filters = request.json['filters']
    else:
        filters = None

    filtered_states = {}
    for agent_id, agent_dict in agent_states.items():
        state_dict = agent_dict['state']
        filtered_state_dict = __filter_dict(state_dict, props, filters)
        filtered_states[agent_id] = filtered_state_dict

    return jsonify(filtered_states)


#########################################################################
# MATRX fetch messages api calls
#########################################################################
@app.route('/get_messages/', methods=['GET', 'POST'])
def get_messages_apicall():
    """ Returns chatrooms and chat messages for one agent, or all agents.

    Per chatroom, an offset can be passed from which will only return messages with a higher index than that
     offset.

    Parameters should be passed via GET URL parameters.

    Parameters
    ----------
    agent_id : (optional URL parameter, default None)
        Agent ID string that will make this function only return chatrooms of which that agent is part. Defaults to
        None, returning all chatsrooms and all chat messages.

    chat_offsets : (optional URL parameter, default None)
        It is not efficient to send every message every tick. With this chat_offsets dict the requestee can
        indicate for every chatroom, which messages they already have, such that only new messages can be sent.
        The `chat_offsets` URL parmaeter should be a dict with as keys the chatroom ID, and as values the message offset.
        The message offset is the index of the message.
        Example of a valid dict: {"0": "10", "3": "5"}.
        This returns the message with index 10+ for the chatroom with ID 0 (global chat),
        and messages with index 5+ for chatroom with ID 3.
    Returns
    -------
        Returns a dictionary with chatrooms and per chatroom a list per with messages.
        The dict is in the shape of: {chatroom_ID: [Message1, Message2, ..], chatroom_ID2 : ....}

        Also see the documentation of the
        :func:`~matrx.utils.message_manager.MessageManager.MyClass.fetch_messages` and
        :func:`~matrx.utils.message_manager.MessageManager.MyClass.fetch_chatrooms` functions.
    """

    # from GET requests fetch URL parameters
    if request.method == "GET":
        error_mssg = f"The /get_messages/ API call only allows POST requests for MATRX Version 2.0.0 and higher. " \
                     f"Please see https://matrx-software.com/docs/upgrading-matrx on how to upgrade."
        print("api request not valid:", error_mssg)
        return abort(400, description=error_mssg)

    # For POST requests fetch json data
    elif request.method == "POST":
        data = request.json
        agent_id = None if "agent_id" not in data else data['agent_id']
        chat_offsets = None if "chat_offsets" not in data else data['chat_offsets']

    else:
        error_mssg = f"API call only allows POST requests."
        print("api request not valid:", error_mssg)
        return abort(400, description=error_mssg)

    chatrooms, messages = get_messages(agent_id, chat_offsets)

    return jsonify({"chatrooms": chatrooms, "messages": messages})


def get_messages(agent_id, chat_offsets):
    """ See :func:`~matrx.api..message_manager.get_messages` """

    # validate agent_id: None or str
    if not isinstance(agent_id, str) and not agent_id is None:
        error_mssg = f"Agent_id passed to /get_messages API request is not of valid format: {agent_id}. " \
                     f"Should be string or not passed."
        print("api request not valid:", error_mssg)
        return abort(400, description=error_mssg)

    if not isinstance(chat_offsets, dict) and not chat_offsets is None:
        error_mssg = f"Chatroom message chat_offsets passed to /get_messages API request is not of valid format: " \
                     f"{chat_offsets}. Should be a dict or not passed."
        print("api request not valid:", error_mssg)
        print(chat_offsets)
        return abort(400, description=error_mssg)

    # fetch chatrooms with messages for the passed agent_id and return it
    chatrooms = gw_message_manager.fetch_chatrooms(agent_id=agent_id)
    messages = gw_message_manager.fetch_messages(agent_id=agent_id, chatroom_mssg_offsets=chat_offsets)

    return chatrooms, messages


# @app.route('/get_messages/<tick>/<agent_id>', methods=['GET'])
# @app.route('/get_messages/<tick>', methods=['GET', 'POST'])
# @app.route('/get_messages/<agent_id>', methods=['GET', 'POST'])
# @app.route('/get_latest_messages', methods=['GET', 'POST'])
# @app.route('/get_latest_messages/<agent_id>', methods=['GET', 'POST'])
# def deprecated_get_messages(agent_id):
#     #TODO: deprecated
#     return jsonify(True)


#########################################################################
# MATRX user input api calls
#########################################################################

@app.route('/send_userinput/<agent_ids>', methods=['POST'])
def send_userinput(agent_ids):
    """ Can be used to send user input from the user (pressed keys) to the specified human agent(s) in MATRX

    Parameters
    ----------
    agent_ids
        ID(s) of the human agent(s) to which the data should be passed.

    Returns
    -------
        returns True if the data was valid (right now always)
    -------

    """
    global userinput

    api_call_valid, error = check_states_API_request(current_tick, agent_ids, ids_required=True)
    if not api_call_valid:
        print("api request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    # make sure the ids are a list
    try:
        agent_ids = eval(agent_ids)
    except:
        agent_ids = [agent_ids]

    # fetch the data from the request object
    data = request.json

    # add each pressed key as user input for each specified human agent
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
    """ Send a message containing information to one or multiple specific agent, the agent's team, or all agents.

    Message as defined in matrx.utils.message

    Returns
    -------
        Error if api call invalid, or True if valid.
    """
    # fetch the data
    data = request.json

    print("Received message to send with data:", data)

    # check that all required parameters have been passed
    required_params = ("content", "sender", "receiver")
    if not all(k in data for k in required_params):
        error = {"error_code": 400, "error_message": f"Missing one of the required parameters: {required_params}"}
        print("api request not valid:", error)
        return abort(error['error_code'], description=error['error_message'])

    # create message
    msg = Message(content=data['content'], from_id=data['sender'], to_id=data['receiver'])

    # add the received_messages to the api global variable
    if data['sender'] not in received_messages:
        received_messages[data['sender']] = []
    received_messages[data['sender']].append(msg)

    return jsonify(True)


#########################################################################
# MATRX context menu API calls
#########################################################################
@app.route('/fetch_context_menu_of_self', methods=['POST'])
def fetch_context_menu_of_self():
    """ Fetch the context menu opened for a specific object/location of the agent being controlled by the user.
    """
    # fetch the data
    data = request.json

    # check that all required parameters have been passed
    required_params = ("agent_id_who_clicked", "clicked_object_id", "click_location", "self_selected")
    if not all(k in data for k in required_params):
        return return_error(code=400, message=f"Missing one of the required parameters: {required_params}")

    agent_id_who_clicked = data['agent_id_who_clicked']
    clicked_object_id = data['clicked_object_id']
    click_location = data['click_location']
    self_selected = data['self_selected']

    # check if agent_id_who_clicked exists in the gw
    if agent_id_who_clicked not in gw.registered_agents.keys() and agent_id_who_clicked != "god":
        return return_error(code=400, message=f"Agent with ID {agent_id_who_clicked} does not exist.")

    # check if it is a human agent
    if agent_id_who_clicked in gw.registered_agents.keys() and \
            not gw.registered_agent_keys[agent_id_who_clicked].is_human_agent:
        return return_error(code=400, message=f"Agent with ID {agent_id_who_clicked} is not a human agent and thus does"
                                              f" not have a context_menu_of_self() function.")

    # ignore if called from the god view
    if agent_id_who_clicked.lower() == "god":
        return return_error(code=400,
                            message=f"The god view is not an agent and thus cannot show its own context menu.")

    # fetch context menu from agent
    context_menu = gw.registered_agents[agent_id_who_clicked].create_context_menu_for_self_func(clicked_object_id,
                                                                                                click_location,
                                                                                                self_selected)

    # encode the object instance of the message
    for item in context_menu:
        item['Message'] = jsonpickle.encode(item['Message'])

    return jsonify(context_menu)


@app.route('/fetch_context_menu_of_other', methods=['POST'])
def fetch_context_menu_of_other():
    """ Fetch the context menu opened for a specific object/location of the agent being controlled by the user.
    """
    # fetch the data
    data = request.json

    # check that all required parameters have been passed
    required_params = ("agent_id_who_clicked", "clicked_object_id", "click_location", "agent_selected")
    if not all(k in data for k in required_params):
        return return_error(code=400, message=f"Missing one of the required parameters: {required_params}")

    agent_id_who_clicked = data['agent_id_who_clicked']
    clicked_object_id = data['clicked_object_id']
    click_location = data['click_location']
    agent_selected = data['agent_selected']

    # check if agent_id_who_clicked exists in the gw
    if agent_id_who_clicked not in gw.registered_agents.keys() and agent_id_who_clicked != "god":
        return return_error(code=400, message=f"Agent with ID {agent_id_who_clicked} does not exist.")

    # check if the selected agent exists
    if agent_selected not in gw.registered_agents.keys():
        return return_error(code=400, message=f"Selected agent with ID {agent_selected} does not exist.")

    # ignore if called from the god view
    # if agent_id_who_clicked.lower() == "god":
    #     return return_error(code=400, message=f"The god view is not an agent and thus cannot show its own context menu.")

    # fetch context menu from agent
    context_menu = gw.registered_agents[agent_selected].create_context_menu_for_other_func(agent_id_who_clicked,
                                                                                           clicked_object_id,
                                                                                           click_location)

    # encode the object instance of the message
    for item in context_menu:
        item['Message'] = jsonpickle.encode(item['Message'])

    return jsonify(context_menu)


@app.route('/send_message_pickled', methods=['POST'])
def send_message_pickled():
    """ This function makes it possible to send a custom message to a MATRX agent via the API as a jsonpickle object.
    For instance, sending a custom message when a context menu option is clicked.
    The pre-formatted CustomMessage instance can be jsonpickled and sent via the API.
    This API call can handle that request and send the CustomMessage to the MATRX agent

    Returns
    -------
        Error if api call invalid, or True if valid.
    """

    # fetch the data
    data = request.json
    print(data)

    # check that all required parameters have been passed
    required_params = ("sender", "message")
    if not all(k in data for k in required_params):
        return return_error(code=400, message=f"Missing one of the required parameters: {required_params}")

    sender_id = data['sender']
    mssg = jsonpickle.decode(data['message'])

    # add the received_messages to the api global variable
    if sender_id not in received_messages:
        received_messages[sender_id] = []
    received_messages[sender_id].append(mssg)

    return jsonify(True)


#########################################################################
# MATRX control api calls
#########################################################################


@app.route('/pause', methods=['GET', 'POST'])
def pause_MATRX():
    """ Pause the MATRX simulation

    Returns
        True if paused, False if already paused
    -------
    """
    global matrx_paused
    if not matrx_paused:
        matrx_paused = True
        return jsonify(True)
    else:
        return jsonify(False)


@app.route('/start', methods=['GET', 'POST'])
def start_MATRX():
    """ Starts / unpauses the MATRX simulation

    Returns
        True if it has been started, False if it is already running
    -------

    """
    global matrx_paused
    if matrx_paused:
        matrx_paused = False
        return jsonify(True)
    else:
        return jsonify(False)


@app.route('/stop', methods=['GET', 'POST'])
def stop_MATRX():
    """ Stops MATRX scenario

    Returns
        True
    -------
    """
    global matrx_done
    matrx_done = True
    return jsonify(True)


@app.route('/change_tick_duration/<tick_dur>', methods=['GET', 'POST'])
def change_MATRX_speed(tick_dur):
    """ Change the tick duration / simulation speed of MATRX

    Parameters
    ----------
    tick_dur
        The duration of 1 tick

    Returns
    -------
        True if successfully changed tick speed (400 error if tick_duration not valid)

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
    """ Shuts down the api by stopping the Flask thread

    Returns
        True
    -------
    """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Unable to shutdown api server. Not running with the Werkzeug Server')
    func()
    print("api server shutting down...")
    return jsonify(True)


#########################################################################
# Errors
#########################################################################

@app.errorhandler(400)
def bad_request(e):
    print("Throwing error", e)
    return jsonify(error=str(e)), 400


def return_error(code, message):
    """ A helper function that returns a specified error code and message """
    if debug:
        print(f"api request not valid: code {code}. Message: {message}.")
    return abort(code, description=message)


#########################################################################
# api helper methods
#########################################################################


def clean_input_ids(ids):
    """ Clean a received api variable ids to valid Python code

    Parameters
    ----------
    ids
        Can be a string (1 agent id), string encoded list (containing agent ids), list with agent ids, or None

    Returns
    -------
        None or list with string agent IDs

    """
    if ids is None:
        return None

    try:
        ids = eval(ids)
    except:
        pass

    # if it is a list
    if isinstance(ids, list):
        return ids

    if isinstance(ids, str):
        return [ids]


def check_messages_API_request(tick=None, agent_id=None):
    """ Checks if the variables of the api request are valid, and if the requested information exists

    Parameters
    ----------
    tick

    agent_id

    Returns
    -------

    """
    if gw_message_manager is None:
        return False, {'error_code': 400,
                       'error_message': f'MATRX hasn\'t started yet.'}

    tick = current_tick if tick is None else tick
    # check user input, such as tick
    check_passed, error_message = check_input(tick)
    if not check_passed:
        return False, error_message

    return True, None


def check_states_API_request(tick=None, ids=None, ids_required=False):
    """ Checks if the variables of the api request are valid, and if the requested information exists

    Parameters
    ----------
    tick
        MATRX tick
    ids
        string with 1 agent ID, or list of agent IDS
    ids_required
        Whether IDS are required

    Returns
    -------
        Success (Boolean indicating whether it is valid or not), Error (if any, prodiving the type and a message)
        See for the error codes:
        https://www.ibm.com/support/knowledgecenter/SS42VS_7.3.0/com.ibm.qradar.doc/c_rest_api_errors.html


    """
    if gw_message_manager is None:
        return False, {'error_code': 400,
                       'error_message': f'MATRX hasn\'t started yet.'}

    # check user input, such as tick and agent id
    check_passed, error_message = check_input(tick)
    if not check_passed:
        return False, error_message

    # Don't throw an error if MATRX is paused the first tick, and thus still has no states
    # if current_tick is 0 and matrx_paused:
    #     return True, None

    # if this api call requires ids, check this variable on validity as well
    if ids_required:

        # check if ids variable is of a valid type
        try:
            ids = eval(ids)
        except:
            pass
            # return False, {'error_code': 400, 'error_message': f'Provided IDs are not of valid format. Provides IDs
            # is of ' f'type {type(ids)} but should be either of type string for ' f'requesting states of 1 agent (
            # e.g. "god"), or a list of ' f'IDs(string) for requesting states of multiple agents'}

        # check if the api was reset during this time
        if len(states) is 0:
            return False, {'error_code': 400,
                           'error_message': f'api is reconnecting to a new world'}

        # check if the provided ids exist for all requested ticks
        ids = [ids] if isinstance(ids, str) else ids
        for t in range(tick, current_tick + 1):
            for id in ids:

                if id not in states[t]:
                    return False, {'error_code': 400,
                                   'error_message': f'Trying to fetch the state for agent with ID "{id}" for tick {t}, '
                                                    f'but no data on that agent exists for that tick. Is the agent ID '
                                                    f'correct?'}

    # all checks cleared, so return with success and no error message
    return True, None


def check_input(tick=None, ids=None):
    """
    Checks if the passed parameters are valid.

    Parameters
    ----------
    tick: integer. Optional
        Tick for which to fetch a state or message. Checks for existence.
    ids: List. Optional
        Agent IDs to check.

    Returns
    -------
    Validity: Boolean.
        Whether the tick and/or agent IDs are valid
    """

    if tick is not None:
        try:
            tick = int(tick)
        except:
            return False, {'error_code': 400,
                           'error_message': f'Tick has to be an integer, but is of type {type(tick)}'}

        # check if the tick has actually occurred
        if not tick in range(0, current_tick + 1):
            return False, {'error_code': 400,
                           'error_message': f'Indicated tick does not exist, has to be in range 0 - {current_tick}, '
                                            f'but is {tick}'}

        # check if the tick was stored
        if tick not in states.keys():
            return False, {'error_code': 400,
                           'error_message': f'Indicated tick {tick} is not stored, only the {nr_states_to_store} ticks '
                                            f'are stored that occurred before the current tick {current_tick}'}

    return True, None


def __fetch_states(tick, ids=None):
    """ This private function fetches, filters and orders the states as specified by the tick and agent ids.

    Parameters
    ----------
    tick
        Tick from which onwards to return the states. Thus will return a list of length [tick:current_tick]. The `tick`
        will checked for whether it was actually stored. If not, an exception is raised.
    ids
        Id(s) from agents/god for which to return the states. Either a single agent ID or a list of agent IDs.
        God view = "god"

    Returns
    -------
        Returns a list of length [tick:current_tick]. For each tick, a dictionary contains the states for each agent as
        specified in `agent_ids`, indexed by their agent ID.

    """
    # Verify tick
    check_passed, error_message = check_input(tick)
    if not check_passed:
        return False, error_message
    tick = int(tick)

    # return all states
    if ids is None:
        # Get the right states based on the tick and return them
        return_states = [state for t, state in states.items() if t >= tick <= current_tick]
        return return_states

    # convert ints to lists so we can use 1 uniform approach
    try:
        ids = eval(ids)
    except:
        ids = [ids]

    # create a list containing the states from tick to current_tick containing the states of all desired agents/god
    filtered_states = []
    for t in range(tick, current_tick + 1):
        states_this_tick = {}

        # add each agent's state for this tick
        for agent_id in ids:
            if agent_id in states[t]:
                states_this_tick[agent_id] = states[t][agent_id]

        # save the states of all filtered agents for this tick
        filtered_states.append(states_this_tick)

    return filtered_states


def __filter_dict(state_dict, props, filters):
    """ Filters a state dictionary to only a dict that contains props for all
    objects that adhere to the filters. A filter is a combination of a
    property and value."""

    def find(obj_dict_pair):
        # Get the object properties
        obj_dict = obj_dict_pair[1]

        # Check if all the desirable properties are in the object dict
        if not all([p in obj_dict.keys() for p in props]):
            return None

        # Check if any filter property is present, if so check its value
        def filter_applies(filter_):
            filter_prop = filter_[0]
            filter_val = filter_[1]
            if filter_prop in obj_dict.keys():
                return filter_val == obj_dict[filter_prop] \
                       or filter_val in obj_dict[filter_prop]
            else:
                return False  # if filter is not present, we return False

        # If filters are given, go over each filter to see if it applies
        if filters is not None:
            filter_results = map(filter_applies, filters.items())

            # Check if all filters are either not applicable or return true
            applies = all(filter_results)
            if applies is False:  # if it does not adhere to the filters
                return None

        # Filter the dict to only the required properties
        new_dict = {p: obj_dict[p] for p in props}

        # Return the new tuple
        return obj_dict_pair[0], new_dict

    # Map our find method to all state objects
    filtered_objects = map(find, state_dict.items())

    # Extract all state objects that have the required properties and adhere to
    # the filters
    objects = [obj_dict_pair for obj_dict_pair in filtered_objects
               if obj_dict_pair is not None]

    # Transform back to dict
    objects = {obj_id: obj_dict for obj_id, obj_dict in objects}

    # Return
    return objects


def create_error_response(code, message):
    """ Creates an error code with a custom message """
    response = jsonify({'message': message})
    response.status_code = code
    return response


def __reorder_state(state):
    """ This private function makes the MATRX state ready for sending as a JSON object

    Parameters
    ----------
    state
         The world state, a dictionary with object IDs as keys

    Returns
    -------
        The world state, JSON serializable
    """
    new_state = copy.copy(state)

    # loop through all objects in the state
    for objID, obj in state.items():

        if objID is not "World":
            # make the sense capability JSON serializable
            if "sense_capability" in obj:
                new_state[objID]["sense_capability"] = str(obj["sense_capability"])

    return new_state


def add_state(agent_id, state, agent_inheritence_chain, world_settings):
    """ Saves the state of an agent for use via the api

    Parameters
    ----------
    agent_id
         ID of the agent of who the state is
    state
        state as filtered by the agent
    agent_inheritence_chain
         inheritance_chain of classes, can be used to figure out type of agent
    world_settings
        This object contains all information on the MATRX world, such as tick and grid_size. Some agents might filter
        these out of their state, as such it is sent along seperatly to make sure the world settings, required by the
        visualization, are passed along.
    """
    # save the new general info on the MATRX World (once)
    global next_tick_info
    if next_tick_info == {}:
        next_tick_info = world_settings

    # Make sure the world settings are in the state, as these are used by the visualization
    if 'World' not in state:
        state['World'] = world_settings

    # state['World']['matrx_paused'] = matrx_paused

    # reorder and save the new state along with some meta information
    temp_state[agent_id] = {'state': __reorder_state(state), 'agent_inheritence_chain': agent_inheritence_chain}


def next_tick():
    """ Proceed to the next tick, publicizing data of the new tick via the api (the new states).
    """
    # save the new general info
    global MATRX_info, next_tick_info, states
    MATRX_info = copy.copy(next_tick_info)
    next_tick_info = {}
    # print("Next ticK:", MATRX_info);

    # publicize the states of the previous tick
    states[current_tick] = copy.copy(temp_state)

    # Limit the states stored
    if len(states) > nr_states_to_store:
        stored_ticks = list(states.keys())
        forget_from = current_tick - nr_states_to_store
        for tick in stored_ticks:
            if tick <= forget_from:
                states.pop(tick)


def pop_userinput(agent_id):
    """ Pop the user input for an agent from the userinput dictionary and return it

    Parameters
    ----------
    agent_id
        ID of the agent for which to return the userinput

    Returns
    -------
        A list of keys pressed. See this link for the encoding of keys:
        https://developer.mozilla.org/nl/docs/Web/API/KeyboardEvent/key/Key_Values
    """
    global userinput
    return userinput.pop(agent_id, None)


def reset_api():
    """ Reset the MATRX api variables """
    global temp_state, userinput, matrx_paused, matrx_done, states, current_tick, tick_duration, grid_size, \
        nr_states_to_store
    global MATRX_info, next_tick_info, received_messages, current_world_ID
    temp_state = {}
    userinput = {}
    matrx_paused = False
    matrx_done = False
    states = {}
    current_tick = 0
    tick_duration = 0.0
    grid_size = [1, 1]
    nr_states_to_store = 5
    MATRX_info = {}
    next_tick_info = {}
    received_messages = {}
    current_world_ID = False


def register_world(world_id):
    """ Register a new simulation world

    At the moment simulation of only one world at a time is supported, so this calling this function will discard
    the previous world.

    Parameters
    ----------
    world_id
        The ID of the world
    """
    global current_world_ID
    current_world_ID = world_id


#########################################################################
# api Flask methods
#########################################################################

def flask_thread():
    """ Starts the Flask server on localhost:3001
    """
    if not debug:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


def run_api(verbose=False):
    """ Creates a separate Python thread in which the api (Flask) is started
    Returns
    -------
        MATRX api Python thread
    """
    print("Starting background api server")
    global debug
    debug = verbose

    print("Initialized app:", app)
    api_thread = threading.Thread(target=flask_thread)
    api_thread.start()
    return api_thread


if __name__ == "__main__":
    run_api()
