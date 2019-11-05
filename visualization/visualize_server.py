import threading
from gevent import sleep

from flask import Flask, render_template

'''
This file holds the code for the MATRXS RESTful API. 
External scripts can send POST and/or GET requests to retrieve state, tick and other information, and send 
userinput or other information to MATRXS. The API is a Flask (Python) webserver.

For visualization, see the seperate MATRXS visualization folder / package.
'''

debug = True
runs = True  # TODO : bool to stop the API during runtime

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


#########################################################################
# Visualization Flask methods
#########################################################################

def flask_thread():
    """
    Starts the Flask server on localhost:3000
    """
    app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False)

def run_api():
    """
    Creates a seperate Python thread in which the API (Flask) is started
    :return: MATRXS API Python thread
    """
    print("Starting background API server")
    global runs
    runs = True

    print("Initialized app:", app)
    API_thread = threading.Thread(target=flask_thread)
    API_thread.start()
    return API_thread

if __name__ == "__main__":
    run_api()