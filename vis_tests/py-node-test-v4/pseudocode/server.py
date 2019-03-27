

# Python server which serves files
# dynamically serve files, based on scenario manager agents?


user_inputs = []


@socketio.on('input')
def user_inputs(id, data):
    # catch user inputs
    # Sort based on agent idea
    # save to var
    user_inputs[id] = data
    pass


# API for testbed Python mainloop
# https://stackoverflow.com/questions/10313001/is-it-possible-to-make-post-request-in-flask
@app.route('/update/<id>', methods = ['POST'])
def update_text(id, data):
    return update_client(id, data)


# function for updating clients
def update_client(id, data):
    # send update with new data to the client (/agent)
    socket.emit(id, data)
    # return user inputs for that agent (if any)
    return user_inputs[id]


def main():
    run_app()
