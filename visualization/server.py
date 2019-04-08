from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO, join_room, emit
from time import sleep, time
import numpy as np
import json
import datetime

# Using PyCharm:
# runfile('visualization/server.py')

# app = Flask(__name__)
app = Flask(__name__, template_folder='static/templates')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

debug = False

grid_sz = [4, 4]

# When you want to emit from a regular route you have to use socketio.emit(),
# only socket handlers have the socketio context necessary to call the plain emit().


###############################################
# Routes initialization
###############################################
@app.route('/init', methods=['POST'])
def init_GUI():

    # pass testbed init to clients / GUIs
    data = request.json
    # socketio.emit('init', data, namespace="/humanagent")
    # socketio.emit('init', data, namespace="/agent")
    # socketio.emit('init', data, namespace="/god")

    global grid_sz
    grid_sz = data["params"]["grid_size"]

    print("Testbed GUI intialization received. Grid size:", grid_sz)

    return ""


###############################################
# Route for receiving testbed updates
###############################################
@app.route('/update', methods=['POST'])
def update_GUI():

    if debug:
        print("Received update from testbed")

    # Fetch data from message
    data = request.json
    god = data["god"]
    agent_states = data["agent_states"]
    hu_ag_states = data["hu_ag_states"]

    # send update to god
    new_data = {'params': {"grid_size": grid_sz}, 'state': god}
    socketio.emit('update', new_data, namespace="/god")


    # send updates to agents
    for agent_id in agent_states:
        new_data = {'params': {"grid_size": grid_sz}, 'state': agent_states[agent_id]}
        room = f"/agent/{agent_id}"
        socketio.emit('update', new_data, room=room, namespace="/agent")


    # send updates to human agents
    for hu_ag_id in hu_ag_states:
        new_data = {'params': {"grid_size": grid_sz}, 'state': hu_ag_states[hu_ag_id]}
        room = f"/humanagent/{hu_ag_id}"
        socketio.emit('update', new_data, room=room, namespace="/humanagent")


    # return user inputs
    global userinput
    resp = jsonify(userinput)
    userinput = {}
    return resp


###############################################
# Routes human agent
###############################################

# update API of Python server / client / GUI
# receives testbed update, passes it on to client / GUI
# returns last userinput (if any)
# @app.route('/update/human-agent/<id>', methods=['POST'])
# def update_human_agent(id):
#     # print("Human Agent update request with agent id:", id)
#
#     # pass testbed update to client / GUI
#     data = request.json
#     data["params"]["grid_size"] = grid_sz
#     room = f"/humanagent/{id}"
#     socketio.emit('update', data, room=room, namespace="/humanagent")
#
#     # send back user input to testbed
#     return format_usr_inp(id)


# route for agent, get the ID from the URL
@app.route('/human-agent/<id>')
def human_agent_view(id):
    return render_template('human_agent.html', id=id)


###############################################
# Routes Agent
###############################################

# update API of Python server / client / GUI
# receives testbed update, passes it on to client / GUI
# returns last userinput (if any)
# @app.route('/update/agent/<id>', methods=['POST'])
# def update_agent(id):
#     # print("Agent update request with agent id:", id)
#
#     # pass testbed update to client / GUI of agent with specified ID
#     data = request.json
#     data["params"]["grid_size"] = grid_sz
#     room = f"/agent/{id}"
#     socketio.emit('update', data, room=room, namespace="/agent")
#
#     # send back user input to testbed
#     return ""


# route for agent, get the ID from the URL
@app.route('/agent/<id>')
def agent_view(id):
    return render_template('agent.html', id=id)


###############################################
# Routes God
###############################################

# update API of Python server / client / GUI
# receives testbed update, passes it on to client / GUI
# returns last userinput (if any)
# @app.route('/update/god', methods=['POST'])
# def update_god():
#
#     # pass testbed update to client / GUI of Godview
#     data = request.json
#     # add grid size
#     data["params"]["grid_size"] = grid_sz
#     socketio.emit('update', data, namespace="/god")
#
#     return ""


# route for agent, get the ID from the URL
@app.route('/god')
def god_view():
    return render_template('god.html')



###############################################
# Managing rooms (connections for a specific agent)
###############################################
# add client to a room for their specific (human) agent ID
@socketio.on('join', namespace='/agent')
@socketio.on('join', namespace='/humanagent')
def join(message):
    join_room(message['room'])
    print("Added client to room:", message["room"])




###############################################
# User input handling for human agent
###############################################

# can't be None, otherwise Flask flips out when returning it
userinput = {}


# # return the userinput from a specific agent by ID as a JSON obj
# def format_usr_inp(id):
#     global userinput
#
#     # check if there is any userinput for this agent
#     if id not in userinput:
#         return jsonify({})
#
#     # convert to a JSON object
#     resp = jsonify(userinput[id])
#
#     # remove the userinput so it doesn't do the same action for infinity
#     del userinput[id]
#
#     return resp


@socketio.on('userinput', namespace="/humanagent")
def handle_usr_inp(input):
    if debug:
        print('received userinput: %s' % input)

    id = input['id']
    action = input['action']

    # save the userinput action to the userinput dict of that human agent.
    # As the agent can do only 1 action at a time remember only the latest
    # userinput action of each human agent
    global userinput
    if id not in userinput:
        userinput[id] = {"action": action}
    else:
        userinput[id]["action"] = action



@socketio.on('connect')
def test_connect():
    print('A client has connected')


if __name__ == "__main__":
    print("Starting server")
    socketio.run(app, host='0.0.0.0', port=3000)
