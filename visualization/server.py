from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO
from time import sleep
import numpy as np
import json

# app = Flask(__name__)
app = Flask(__name__, template_folder='static/templates')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


###############################################
# Routes human agent
###############################################

# update API of Python server / client / GUI
# receives testbed update, passes it on to client / GUI
# returns last userinput (if any)
@app.route('/update/human-agent/<id>', methods=['POST'])
def update_human_agent(id):
    print("Human Agent update request with agent id:", id)

    # pass testbed update to client / GUI
    data = request.json
    socketio.emit('update', data, namespace=f"/human-agent/{id}")

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
    socketio.emit('update', data, namespace=f"/agent/{id}")

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


@socketio.on('userinput')
def handle_usr_inp(input):
    # print('received userinput: %s' % input)

    id = input['id']
    movement = input['movement']

    # save the movement to the userinput of that human agent
    # agent can do only 1 action at a time, so remember only the latest
    # userinput action of each human agent
    global userinput
    if id not in userinput:
        userinput[id] = {"movement": movement}
    else:
        userinput[id]["movement"] = movement



@socketio.on('connect')
def test_connect():
    print('got a connect')
    socketio.emit('my response', {'data': 'Connected'})


if __name__ == "__main__":
    print("Starting server")
    socketio.run(app, port=3000)
