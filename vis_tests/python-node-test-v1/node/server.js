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
app.get('/agent', function(request, response) {
  response.sendFile(path.join(__dirname + '/static', 'agent.html'));
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
setInterval(function() {
  io.sockets.emit('message', 'hi!');
}, 1000);

//
// //server.js
// var app = require('express')();
// var http = require('http').Server(app);
// var io = require('socket.io')(http);
//
// io.on('connection', function (socket){
//    console.log('connection made');
//
//   socket.on('CH01', function (from, msg) {
//     console.log('MSG', from, ' saying ', msg);
//   });
//
//   socket.on('test', function (from, msg) {
//     console.log("we got test");
//   });
//
// });

// http.listen(3000, function () {
//   console.log('listening on *:3000');
// });
