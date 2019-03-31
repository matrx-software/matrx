from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO, join_room, emit
from time import sleep
import numpy as np
import json

# app = Flask(__name__)
app = Flask(__name__, template_folder='static/templates')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


# When you want to emit from a regular route you have to use socketio.emit(),
# only socket handlers have the socketio context necessary to call the plain emit().


###############################################
# Routes human agent
###############################################

# update API of Python server / client / GUI
# receives testbed update, passes it on to client / GUI
# returns last userinput (if any)
@app.route('/update/human-agent/<id>', methods=['POST'])
def update_human_agent(id):
    # print("Human Agent update request with agent id:", id)

    # pass testbed update to client / GUI
    data = request.json
    room = f"/humanagent/{id}"
    socketio.emit('update', data, room=room, namespace="/humanagent")

    # send back user input to testbed
    return format_usr_inp(id)


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
@app.route('/update/agent/<id>', methods=['POST'])
def update_agent(id):
    # print("Agent update request with agent id:", id)

    # pass testbed update to client / GUI of agent with specified ID
    data = request.json
    room = f"/agent/{id}"
    socketio.emit('update', data, room=room, namespace="/agent")

    # send back user input to testbed
    return ""


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
@app.route('/update/god', methods=['POST'])
def update_god():

    # pass testbed update to client / GUI of Godview
    data = request.json
    socketio.emit('update', data, namespace="/god")

    return ""


# route for agent, get the ID from the URL
@app.route('/god')
def god_view():
    return render_template('god.html')



###############################################
# Managing rooms
###############################################
# add client to a room for their specific (human) agent ID
@socketio.on('join', namespace='/agent')
@socketio.on('join', namespace='/humanagent')
def join(message):
    join_room(message['room'])
    print("Added client to room:", message["room"])

    # emit('test', "Hey room " + message['room'] + "!", room=message['room'])
    print("sending message to room", message['room'])




###############################################
# server-client socket connections (agent / humanagent)
###############################################

# can't be None, otherwise Flask flips out when returning it
userinput = {}


# return the userinput from a specific agent by ID as a JSON obj
def format_usr_inp(id):
    global userinput

    # check if there is any userinput for this agent
    if id not in userinput:
        return jsonify({})

    # convert to a JSON object
    resp = jsonify(userinput[id])

    # remove the userinput so it doesn't do the same action for infinity
    del userinput[id]

    return resp


@socketio.on('userinput', namespace="/humanagent")
def handle_usr_inp(input):
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
    print('got a connect')


if __name__ == "__main__":
    print("Starting server")
    socketio.run(app, port=3000)
