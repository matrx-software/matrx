from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO
from time import sleep
import numpy as np

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
@app.route('/update/human-agent/<int:id>', methods=['POST'])
def update_human_agent(id):
    data = request.json

    # pass testbed update to client / GUI
    data = request.json
    socketio.emit('update', data)

    # send back user input to testbed
    return format_usr_inp()


# route for agent, get the ID from the URL
@app.route('/human-agent/<int:id>')
def human_agent_view(id):
    return render_template('human-agent.html', id=id)


###############################################
# Routes Agent
###############################################

# update API of Python server / client / GUI
# receives testbed update, passes it on to client / GUI
# returns last userinput (if any)
@app.route('/update/agent/<id>', methods=['POST'])
def update_agent(id):
    # print("Agent update request with agent id:", id)

    # pass testbed update to client / GUI
    data = request.json
    socketio.emit('update', data)

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

    # pass testbed update to client / GUI
    data = request.json
    socketio.emit('update', data)

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
# userinput = {'movement': 4}

def format_usr_inp():
    global userinput
    resp = jsonify(userinput)
    userinput = {}
    return resp


@socketio.on('userinput')
def handle_usr_inp(input):
    print('received userinput: %s' % input)
    # agent can do only 1 action at a time, so
    # remember only the latest userinput action
    global userinput
    userinput = input


@socketio.on('connect')
def test_connect():
    print('got a connect')
    socketio.emit('my response', {'data': 'Connected'})


if __name__ == "__main__":
    print("Starting server")
    socketio.run(app, port=3000)
