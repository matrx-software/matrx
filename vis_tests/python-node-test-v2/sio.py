from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@socketio.on('test')
def handle_message(message):
    print('received test: ' + message)
    socketio.emit('test', 'hai!')


@socketio.on('connect')
def test_connect():
    print('got a connect')
    socketio.emit('my response', {'data': 'Connected'})


if __name__ == '__main__':
    socketio.run(app, port=3000)
