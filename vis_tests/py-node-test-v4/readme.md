

Testbed main loop
sends an API request to the Python Flask server with updated data (grid world, etc.),
Receives user inputs from API request



Python server (Flask)
receives testbed updates, passes them on to correct agent client, sends back user inputs
receives and safes user inputs from clients



Python clients (agents etc.)
shows GUI with gridworld etc.
receives updates from python server -> updates visuals
catches user inputs and sends them back to the server
