// Dependencies
var express = require('express');
var http = require('http');
var path = require('path');
var socketIO = require('socket.io');

var app = express();
var server = http.Server(app);
var io = socketIO(server);

app.set('port', 5000);
app.use('/static', express.static(__dirname + '/static'));

// Routing
app.get('/', function(request, response) {
  response.sendFile(path.join(__dirname + '/static', 'scenario_manager/index.html'));
});
app.get('/god', function(request, response) {
  response.sendFile(path.join(__dirname + '/static', 'god/index.html'));
});
app.get('/agent', function(request, response) {
  response.sendFile(path.join(__dirname + '/static', 'agent/index.html'));
});


// Starts the server.
server.listen(5000, function() {
  console.log('Starting server on port 5000');
});


// Add the WebSocket handlers
io.on('connection', function(socket) {
    // catch message send from browser
    socket.on('click', function(data) {
        console.log("Button clicked", data);
    });
});

// send message to browser
// setInterval(function() {
//   io.sockets.emit('message', 'hi!');
// }, 1000);
