from flask import Flask
from flask_socketio import SocketIO

from multiprocessing import Process, Value
from time import sleep

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@socketio.on('test')
def handle_message(message):
    print('received test: ' + message)
    # socketio.emit('test', 'hai!')


@socketio.on('connect')
def test_connect():
    print('got a connect')
    socketio.emit('my response', {'data': 'Connected'})

#
# if __name__ == '__main__':
#     socketio.run(app, port=3000)



def record_loop():
    while True:
        print("loop running")
        socketio.emit('test', 'hello from loop')
        sleep(1)



if __name__ == "__main__":
    p = Process(target=record_loop)
    p.start()

    # app.run(debug=True, use_reloader=False)
    socketio.run(app, port=3000)
    p.join()
