$(document).ready(function(){
    // make connection with python server via socket
    var namespace = "/god"
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
});
