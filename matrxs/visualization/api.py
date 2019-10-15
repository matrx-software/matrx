import threading

from flask import Flask, render_template
from flask_socketio import SocketIO

'''
This file holds the code for the Flask (Python) webserver, which listens to grid updates
via a restful API, and forwards these to the specific viewpoint (god, agent, human-agent).
'''

debug = True
runs = True  # TODO : bool to stop the API during runtime

app = None
io_socket = None
async_mode = "gevent"  # gevent (preferred) or eventlet.

# variables to be read and set by MATRXS
states = {}  # TODO Gridworld needs to fill this dict


def flask_thread(app, socket):
    socket.run(app, host='0.0.0.0', port=3000, debug=False, use_reloader=False)


def init_app():
    global app, io_socket
    app = Flask(__name__, template_folder='static/templates')
    app.config['SECRET_KEY'] = 'secret!'
    io_socket = SocketIO(app, async_mode=async_mode)


def state_update():

    # TODO run this loop with the speed of 'tick duration'
    while runs:
        # TODO send a POST request with the states; '/update_states'
        pass


def run_api():
    print("Starting background API server")
    global runs
    runs = True
    init_app()
    thread = threading.Thread(target=flask_thread, args=(app, io_socket))
    thread.start()

    state_update_thread = threading.Thread(target=state_update, args=())
    state_update_thread.start()


if __name__ == "__main__":
    run_api()


@app.route('/init', methods=['POST'])
def init_gui():
    """
    Routes initialisation.

    Returns
    -------
    str
        Empty response.

    """
    pass


@app.route('/update_states', methods=['POST'])
def update_states():
    pass

@app.route('/settings/tick_duration')
def set_tick_duration():
    pass


@app.route('/human-agent/<id>')
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
@app.route('/agent/<id>')
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


@app.route('/god')
def god_view():
    """
    Route for the 'god' view which contains the ground truth of the world without restrictions.

    Returns
    -------
    str
        The template for this view.

    """
    return render_template('god.html')


@app.route('/avatars')
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
