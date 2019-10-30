
from gevent import sleep
from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO, join_room
import threading


'''
This file holds the code for the Flask (Python) webserver, which listens to grid updates
via a restful API, and forwards these to the specific viewpoint (god, agent, human-agent).
'''

debug = True

# overwritten by settings from MATRXS
grid_sz = None  # [4, 4]
vis_bg_clr = None  # "#C2C2C2"
vis_bg_img = None
user_input = {}  # can't be None, otherwise Flask flips out when returning it
async_mode = "gevent" # gevent (preferred) or eventlet.

def create_app():
    #current_folder = os.path.dirname(os.path.abspath(__file__)) # alternative: os.getcwd()
    #template_folder = os.path.join(current_folder, "static", "templates")
    #app = Flask("matrxs", template_folder=template_folder)
    app = Flask(__name__, template_folder='static/templates')
    app.config['SECRET_KEY'] = 'secret!'
    sio = SocketIO(app,async_mode=async_mode)
    return app, sio

def join(message):
    """
    Add client to a room for their specific (human) agent ID

    Parameters
    ----------
    message
        The received message on join event.

    Returns
    -------
    None
        ...

    """
    join_room(message['room'].lower())
    if debug:
        print("Added client to room:", message["room"].lower())


###############################################
# User input handling for human agent
###############################################

#

def handle_usr_inp(input):
    """
    Fetch user input messages sent from human agents

    Parameters
    ----------
    input
        The user input.

    Returns
    -------
    None
        ...

    """
    if debug:
        print('received userinput: %s' % input)

    id = input['id'].lower()
    key_pressed = input['key']

    # save the user input action to the user input dict of that human agent.
    global user_input
    if id not in user_input:
        user_input[id] = []
    # don't add duplicate key presses
    if key_pressed not in user_input[id]:
        user_input[id].append(key_pressed)

    if debug:
        print(f"User input: {user_input[id]}")


# def __start_server():
#
#     try:
#         if debug:
#             print("Server running..")
#         appFlask = AppFlask()
#         appFlask.socketio.run(appFlask.app, host='0.0.0.0', port=3000, debug=False, use_reloader=False)
#         return
#
#     except OSError as err:
#         if "port" in err.strerror:
#             if debug:
#                 warnings.warn("Visualisation server is already running, not starting another visualisation server "
#                               "thread.")
#             return
#         else:
#             raise err

def flaskThread(app, socket):
    socket.run(app, host='0.0.0.0', port=3000, debug=False, use_reloader=False)


def run_visualisation_server():
    print("Starting background vis server")
    appFlask = AppFlask()
    thread =threading.Thread(target=flaskThread, args=(appFlask.app, appFlask.socketio,))
    thread.start()

    return


if __name__ == "__main__":
    #__start_server()
    run_visualisation_server()



class AppFlask:
    def __init__(self):
        self.app, self.socketio = create_app()
        print("Creating socketio app in server.py")

        @self.app.route('/init', methods=['POST'])
        def init_gui():
            """
            Routes initialisation.

            Returns
            -------
            str
                Empty response.

            """

            # pass MATRXS init to clients / GUIs
            data = request.json

            global grid_sz, vis_bg_clr, vis_bg_img
            grid_sz = data["params"]["grid_size"]
            vis_bg_clr = data["params"]["vis_bg_clr"]
            vis_bg_img = data["params"]["vis_bg_img"]
            if debug:
                print("Testbed GUI initialization received. Grid size:", grid_sz, " Visualization BG colour:",
                      vis_bg_clr,
                      " Visualization BG image:", vis_bg_img)
            return ""

        @self.app.route('/update', methods=['POST'])
        def update_gui():
            """
            Route for receiving MATRXS updates

            Returns
            -------
            str
                JSON string with the user input response.

            """

            if debug:
                print("Received update from MATRXS")

            # Fetch data from message
            data = request.json
            god_state = data["god"]
            agent_states = data["agent_states"]
            hu_ag_states = data["hu_ag_states"]
            tick = data['tick']

            # send update to god view
            new_data = {
                'params': {"grid_size": grid_sz, "tick": tick, "vis_bg_clr": vis_bg_clr, "vis_bg_img": vis_bg_img},
                'state': god_state}

            self.socketio.emit('update', new_data, namespace="/god")
            sleep()
            #send updates to agent view
            for agent_id in agent_states:
                new_data = {
                    'params': {"grid_size": grid_sz, "tick": tick, "vis_bg_clr": vis_bg_clr, "vis_bg_img": vis_bg_img},
                    'state': agent_states[agent_id]}
                room = f"/agent/{agent_id.lower()}"
                # print(f"Sending to agent {agent_id} {room}")
                self.socketio.emit('update', new_data, room=room, namespace="/agent")
                sleep()

            # send updates to human agents
            for hu_ag_id in hu_ag_states:
                new_data = {
                     'params': {"grid_size": grid_sz, "tick": tick, "vis_bg_clr": vis_bg_clr, "vis_bg_img": vis_bg_img},
                     'state': hu_ag_states[hu_ag_id]}
                room = f"/humanagent/{hu_ag_id.lower()}"
                # print(f"Sending to human agent {hu_ag_id} {room}")
                self.socketio.emit('update', new_data, room=room, namespace="/humanagent")
                sleep()

            # return user inputs
            global user_input
            resp = jsonify(user_input)
            user_input = {}
            return resp

        @self.app.route('/human-agent/<id>')
        def human_agent_view(id):
            """
            Route for HumanAgentBrain

            Parameters
            ----------
            id
                The human agent ID. Is obtained from the URL.

            Returns
            -------
            str
                The template for this agent's view.

            """
            return render_template('human_agent.html', id=id)

        # route for agent, get the ID from the URL
        @self.app.route('/agent/<id>')
        def agent_view(id):
            """
            Route for AgentBrain

            Parameters
            ----------
            id
                The agent ID. Is obtained from the URL.

            Returns
            -------
            str
                The template for this agent's view.

            """
            return render_template('agent.html', id=id)

        @self.app.route('/god')
        def god_view():
            """
            Route for the 'god' view which contains the ground truth of the world without restrictions.

            Returns
            -------
            str
                The template for this view.

            """
            return render_template('god.html')

        @self.app.route('/avatars')
        # route for agent picture
        def image():
            """
            Rout for the images for agents.

            Returns
            -------
            str
                The image template.

            """
            return render_template('avatars.html')

        @self.socketio.on('join', namespace='/agent')
        @self.socketio.on('join', namespace='/humanagent')
        def join(message):
            """
            Add client to a room for their specific (human) agent ID

            Parameters
            ----------
            message
                The received message on join event.

            Returns
            -------
            None
                ...

            """
            join_room(message['room'].lower())
            if debug:
                print("Added client to room:", message["room"].lower())
        ###############################################
        # User input handling for human agent
        ###############################################

        @self.socketio.on('userinput', namespace="/humanagent")
        def handle_usr_inp(input):
            """
            Fetch user input messages sent from human agents

            Parameters
            ----------
            input
                The user input.

            Returns
            -------
            None
                ...

            """
            if debug:
                print('received userinput: %s' % input)

            id = input['id'].lower()
            key_pressed = input['key']

            # save the user input action to the user input dict of that human agent.
            global user_input
            if id not in user_input:
                user_input[id] = []
            # don't add duplicate key presses
            if key_pressed not in user_input[id]:
                user_input[id].append(key_pressed)

            if debug:
                print(f"User input: {user_input[id]}")
