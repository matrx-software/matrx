var socket = io();

// get message from server
socket.on('message', function(data) {
  console.log(data);
});

// //client.js
// var io = require('socket.io-client');
// var socket = io.connect('http://localhost:3000', {reconnect: true});
//
// // Add a connect listener
// socket.on('connect', function () {
//     console.log('Connected!');
//     socket.emit("test", {"data":"blob"});
// });
// socket.emit('CH01', 'me', 'test msg');
