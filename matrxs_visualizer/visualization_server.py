import threading
import logging
from flask import Flask, render_template, request, jsonify

'''
This file holds the code for the MATRXS RESTful API. 
External scripts can send POST and/or GET requests to retrieve state, tick and other information, and send 
userinput or other information to MATRXS. The API is a Flask (Python) webserver.

For visualization, see the seperate MATRXS visualization folder / package.
'''

debug = True
port = 3000
app = Flask(__name__, template_folder='static/templates')


#########################################################################
# Visualization server routes
#########################################################################

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


@app.route('/shutdown_visualizer', methods=['GET', 'POST'])
def shutdown():
    """ Shuts down the visualizer by stopping the Flask thread

    Returns
        True
    -------
    """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Unable to shutdown visualizer server. Not running with the Werkzeug Server')
    func()
    print("Visualizer server shutting down...")
    return jsonify(True)



#########################################################################
# Visualization Flask methods
#########################################################################

def flask_thread():
    """
    Starts the Flask server on localhost:3000
    """

    if not debug:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_matrxs_visualizer(verbose):
    """
    Creates a seperate Python thread in which the visualization server (Flask) is started, serving the JS visualization
    :return: MATRXS visualization Python thread
    """
    global debug
    debug = verbose

    print("Starting visualization server")
    print("Initialized app:", app)
    print("Open http://localhost:" + str(port) + "/god for a god-mode view of the active simulation.")
    vis_thread = threading.Thread(target=flask_thread)
    vis_thread.start()
    return vis_thread

if __name__ == "__main__":
    run_matrxs_visualizer()