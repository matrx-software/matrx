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



# POST request via API from testbed python main loop
@app.route('/update/agent/<int:id>', methods=['POST'])
def update_agent(id):
    data = request.json
    params = data['params']
    arr = np.array(data['arr'])
    print(params, arr.shape)

    # print("Received update request for id", id , " with data ")
    # resp = "Response"
    return jsonify(userinput)


# route for agent, get the ID from the URL
@app.route('/agent/<int:id>')
def index(id):
    return render_template('index.html', id=id)





###############################################
# server-client socket connections (agent / humanagent)
###############################################

# can't be None, otherwise Flask flips out when returning it
userinput = {}
userinput = {'movement': 4}

@socketio.on('userinput')
def handle_message(input):
    print('received userinput: %s' % input)

    # agent can do only 1 action at a time, so
    # remember only the latest userinput
    userinput = input

    print("Userinput list currently: %s" % userinput)

@socketio.on('test')
def handle_message(message):
    print('received test: ' + message)
    socketio.emit('test', 'hai!')


@socketio.on('connect')
def test_connect():
    print('got a connect')
    socketio.emit('my response', {'data': 'Connected'})


if __name__ == "__main__":
    print("Starting server")
    socketio.run(app, port=3000)
