from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO
from time import sleep
import numpy as np

# app = Flask(__name__)
app = Flask(__name__, template_folder='static/templates')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


###############################################
# Routes (agent / humanagent / god)
###############################################

# GET request via API from testbed python main loop
@app.route('/example/<int:id>', methods=['GET'])
def example_get(id):
    data = request.args.get('gw')
    print("Received update request for id", id , " with data ", data)
    resp = "Response"
    return resp

# POST request via API from testbed python main loop
@app.route('/example/<int:id>', methods=['POST'])
def example_post(id):
    data = request.args.get('gw')
    print("Received update request for id", id , " with data ", data)
    resp = "Response"
    return resp



# update API of Python server / client / GUI
# receives testbed update, passes it on to client / GUI
# returns last userinput (if any)
@app.route('/update/agent/<int:id>', methods=['POST'])
def update_agent(id):
    data = request.json

    # pass testbed update to client / GUI
    data = request.json
    socketio.emit('update', data)

    # send back user input to testbed
    return format_usr_inp()


# route for agent, get the ID from the URL
@app.route('/agent/<int:id>')
def index(id):
    return render_template('index.html', id=id)





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


@socketio.on('test')
def handle_test(message):
    print('received test: ' + message)
    socketio.emit('test', 'hai!')


@socketio.on('connect')
def test_connect():
    print('got a connect')
    socketio.emit('my response', {'data': 'Connected'})


if __name__ == "__main__":
    print("Starting server")
    socketio.run(app, port=3000)
