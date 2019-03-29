// specify a namespace, so that we only listen to messages from the server for this specific agent
var namespace = "/agent/" + document.getElementById('id').innerHTML;
// make connection with the python server via a (web)socket
var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

// Event handler for new connections.
socket.on('connect', function() {
    console.log("Connected");
});

// receive an update from the python server
socket.on('update', function(data){
    console.log("Received an update from the server:", data);

    grid_size = data.params.grid_size;
    state = data.state;

    // draw the screen again
    requestAnimationFrame(function() {
        drawSim(grid_size, state);
    });
});
