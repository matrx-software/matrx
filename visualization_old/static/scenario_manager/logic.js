var socket = io();

// get message from server
socket.on('message', function(data) {
  console.log(data);
});

// Catch button click
document.getElementById("button").addEventListener("click", function(){
    var target = event.target || event.srcElement;

    console.log("Clicked button:", target.id);

    // send message to server
    socket.emit('click', {"data": "much much data", "data2": "even more data"});
});
