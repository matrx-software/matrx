import threading
from gevent import sleep

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO

'''
This file holds the code for the MATRXS RESTful API. 
External scripts can send POST and/or GET requests to retrieve state, tick and other information, and send 
userinput or other information to MATRXS. The API is a Flask (Python) webserver.

For visualization, see the seperate MATRXS visualization folder / package.
'''

debug = True
runs = True  # TODO : bool to stop the API during runtime

app = Flask(__name__, template_folder='static/templates')
# app = None
# io_socket = None
async_mode = "gevent"  # gevent (preferred) or eventlet.

# variables to be read and set by MATRXS
states = {}  # TODO Gridworld needs to fill this dict
current_tick = 0


def flask_thread():
    app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False)



def run_api():
    print("Starting background API server")
    global runs
    runs = True

    print("Initialized app:", app)
    API_thread = threading.Thread(target=flask_thread)
    API_thread.start()

if __name__ == "__main__":
    run_api()


# @app.route('/get_states', methods=['GET', 'POST'])
# def get_states():
#     return "blabla"
#
#
# @app.errorhandler(400)
# def custom400(error):
#     response = {'message': error.description['message']}


@app.route('/get_states/<tick>', methods=['GET', 'POST'])
def get_states(tick):
    print(f"Sending states from tick {tick} onwards")

    if tick not in states:
        # response = jsonify({'message': f"Tick has not occured yet, current tick is {current_tick}"})
        # response.status_code = 400
        # return response
        return {}

    return "blabla"

@app.route('/get_tick', methods=['GET', 'POST'])
def get_tick():
    print(f"Sending latest tick")
    return "blabla"




# def do_stuff():
#     while True:
#         print("API running in bg thread")
#         sleep(1)



#
# @app.route('/update_states', methods=['POST'])
# def update_states():
#     pass
#
# @app.route('/settings/tick_duration')
# def set_tick_duration():
#     pass
#
#
# @app.route('/human-agent/<id>')
# def human_agent_view(id):
#     """
#     Route for HumanAgentBrain
#
#     Parameters
#     ----------
#     id
#         The human agent ID. Is obtained from the URL.
#
#     Returns
#     -------
#     str
#         The template for this agent's view.
#
#     """
#     return render_template('human_agent.html', id=id)
#
#
# # route for agent, get the ID from the URL
# @app.route('/agent/<id>')
# def agent_view(id):
#     """
#     Route for AgentBrain
#
#     Parameters
#     ----------
#     id
#         The agent ID. Is obtained from the URL.
#
#     Returns
#     -------
#     str
#         The template for this agent's view.
#
#     """
#     return render_template('agent.html', id=id)
#
#
# @app.route('/god')
# def god_view():
#     """
#     Route for the 'god' view which contains the ground truth of the world without restrictions.
#
#     Returns
#     -------
#     str
#         The template for this view.
#
#     """
#     return render_template('god.html')
#
#
# @app.route('/avatars')
# # route for agent picture
# def image():
#     """
#     Rout for the images for agents.
#
#     Returns
#     -------
#     str
#         The image template.
#
#     """
#     return render_template('avatars.html')
