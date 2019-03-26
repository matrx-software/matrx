
const socket = io('http://localhost:3000');

socket.on('connect', function(){
  console.log("Connected");
});


// Check for received messages from Python server
socket.on('test', function(data){
  console.log("got a message:", data);
});


socket.on('disconnect', function(){
  console.log("Disconnected");
});


// send message to Python server
setInterval(function() {
  socket.emit("test", "hey");
  console.log("Sending test");
}, 1000);
