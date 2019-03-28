

Testbed main loop
sends an API request to the Python Flask server with updated data (grid world, etc.),
    + example grid
    - real grid
Receives user inputs from API request
    + done


Python server (Flask)
receives testbed updates, passes them on to correct agent client, sends back user inputs
    + receives testbed updates
    + sends back user inputs
    + pass testbed updates to client
receives and safes user inputs from clients
    + to do


Python clients (agents etc.)
server-client setup
    + serve webpage
    + socket server-client and client-server messages
shows GUI with gridworld etc.
    + to do
receives updates from python server -> updates visuals
    - to do
catches user inputs and sends them back to the server
    + to do



# installation requirements
- eventlet
- flask
- flask_socketio
