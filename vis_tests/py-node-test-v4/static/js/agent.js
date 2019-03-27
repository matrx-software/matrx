// make connection with python server via socket
var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

// Event handler for new connections.
// The callback function is invoked when a connection with the
// server is established.
socket.on('connect', function() {
    socket.emit('my_event', {data: 'I\'m connected!'});
    console.log("Connected");
});

// receive an update from the python server
socket.on('test', function(data){
  console.log("got a message:", data);
});

// send message to Python server every 1 second
// setInterval(function() {
//     socket.emit("test", "yo from agent GUI");
//     console.log("Sending test");
// }, 1000);


// Catch userinput with arrow keys
// Arrows keys: up=1, right=2, down=3, left=4
document.onkeydown = checkArrowKey;
function checkArrowKey(e) {
    e = e || window.event;

    if (e.keyCode == '38') {
        // up arrow
        socket.emit("userinput", {"movement": 1});
    }
    else if (e.keyCode == '39') {
       // right arrow
       socket.emit("userinput", {"movement": 2});
    }
    else if (e.keyCode == '40') {
        // down arrow
        socket.emit("userinput", {"movement": 3});
    }
    else if (e.keyCode == '37') {
       // left arrow
       socket.emit("userinput", {"movement": 4});
    }
}
