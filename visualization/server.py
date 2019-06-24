from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO, join_room, emit
from time import sleep, time
import numpy as np
import json
import datetime


'''
This file holds the code for the Flask (Python) webserver, which listens to grid updates
via a restful API, and forwards these to the specific viewpoint (god, agent, human-agent).
'''



# Using PyCharm:
# runfile('visualization/server.py')

app = Flask(__name__, template_folder='static/templates')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

debug = False

# overwritten by settings from simulator
grid_sz = [4, 4]
vis_bg_clr = "#C2C2C2"

# can't be None, otherwise Flask flips out when returning it
userinput = {}

# When you want to emit from a regular route you have to use socketio.emit(),
# only socket handlers have the socketio context necessary to call the plain emit().


###############################################
# Routes initialization
###############################################
@app.route('/init', methods=['POST'])
def init_GUI():

    # pass testbed init to clients / GUIs
    data = request.json

    global grid_sz, vis_bg_clr
    grid_sz = data["params"]["grid_size"]
    vis_bg_clr = data["params"]["vis_bg_clr"]

    print("Testbed GUI intialization received. Grid size:", grid_sz , " Visualization BG colour:", vis_bg_clr)

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
    tick = data['tick']

    # send update to god
    new_data = {'params': {"grid_size": grid_sz, "tick": tick, "vis_bg_clr": vis_bg_clr}, 'state': god}
    socketio.emit('update', new_data, namespace="/god")


    # send updates to agents
    for agent_id in agent_states:
        new_data = {'params': {"grid_size": grid_sz, "tick": tick, "vis_bg_clr": vis_bg_clr}, 'state': agent_states[agent_id]}
        room = f"/agent/{agent_id.lower()}"
        # print(f"Sending to agent {agent_id} {room}")
        socketio.emit('update', new_data, room=room, namespace="/agent")

    # send updates to human agents
    for hu_ag_id in hu_ag_states:
        new_data = {'params': {"grid_size": grid_sz, "tick": tick, "vis_bg_clr": vis_bg_clr}, 'state': hu_ag_states[hu_ag_id]}
        room = f"/humanagent/{hu_ag_id.lower()}"
        # print(f"Sending to human agent {hu_ag_id} {room}")
        socketio.emit('update', new_data, room=room, namespace="/humanagent")


    # return user inputs
    global userinput
    resp = jsonify(userinput)
    userinput = {}
    return resp


###############################################
# Routes human agent
###############################################

# route for human agent, get the ID from the URL
@app.route('/human-agent/<id>')
def human_agent_view(id):
    return render_template('human_agent.html', id=id)


###############################################
# Routes Agent
###############################################

# route for agent, get the ID from the URL
@app.route('/agent/<id>')
def agent_view(id):
    return render_template('agent.html', id=id)


###############################################
# Routes God
###############################################

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
    join_room(message['room'].lower())
    print("Added client to room:", message["room"].lower())




###############################################
# User input handling for human agent
###############################################

# Fetch userinput messages sent from human agents
@socketio.on('userinput', namespace="/humanagent")
def handle_usr_inp(input):
    if debug:
        print('received userinput: %s' % input)

    id = input['id'].lower()
    keyPressed = input['key']

    # save the userinput action to the userinput dict of that human agent.
    global userinput
    if id not in userinput:
        userinput[id] = []
    # don't add duplicate keypresses
    if keyPressed not in userinput[id]:
        userinput[id].append(keyPressed)

    if debug:
        print(f"Userinput:{userinput[id]}")



@socketio.on('connect')
def test_connect():
    print('A client has connected')


if __name__ == "__main__":
    print("Server running")
    socketio.run(app, host='0.0.0.0', port=3000)
