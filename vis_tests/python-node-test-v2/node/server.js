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
  response.sendFile(path.join(__dirname + '/static', 'agent.html'));
});

// Starts the server.https://www.space.com/amazing-virgin-galactic-launch-video.html
server.listen(5000, function() {
  console.log('Starting server on port 5000');
});
