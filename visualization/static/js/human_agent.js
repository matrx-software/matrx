$(document).ready(function(){

    var id = document.getElementById('id').innerHTML;

    // specify a namespace, so that we only listen to messages from the server for this specific human agent
    var namespace = "/humanagent";

    var grid_sz = [4, 4]

    // make connection with python server via socket to get messages only for the human agent
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    // Event handler for new connections.
    socket.on('connect', function() {
        console.log("Connected");

        var room = "/humanagent/" + id;

        // request to be added to room so the server can send messages specific to this human agent
        console.log("Requesting to be added to room:", room)
        socket.emit('join', {room: room});
    });

    // Event handler for new connections.
    socket.on('init', function(data) {
        console.log("Init grid with grid_size:", grid_sz);

        grid_sz = data.params.grid_size;
    });

    // receive an update from the python server
    socket.on('update', function(data){
        console.log("Received an update from the server:", data);

        // unpack received data
        state = data.state;

        // draw the grid again
        requestAnimationFrame(function() {
            drawSim(grid_sz, state);
        });
    });

    // // receive a test update from the python server
    // socket.on('test', function(data){
    //     console.log("got a message:", data);
    // });

    var id = -1;


    // bind key listener
    document.onkeydown = checkArrowKey;

    // get the ID of the current human_agent from the html
    id = document.getElementById('id').innerHTML;


    /**
     * Catch userinput with arrow keys
     *
     * Arrows keys: up=1, right=2, down=3, left=4
     */
    function checkArrowKey(e) {
        e = e || window.event;

        // filter for arrow keys (for now)
        if (e.keyCode < 37 || e.keyCode > 40) {
            return
        }

        // send an update for every arrow key pressed
        if (e.keyCode == '38') {
            // up arrow
            socket.emit("userinput", {"action": "arrowkey:up", 'id': id});
        }
        else if (e.keyCode == '39') {
           // right arrow
           socket.emit("userinput", {"action": "arrowkey:right", 'id': id});
        }
        else if (e.keyCode == '40') {
            // down arrow
            socket.emit("userinput", {"action": "arrowkey:down", 'id': id});
        }
        else if (e.keyCode == '37') {
           // left arrow
           socket.emit("userinput", {"action": "arrowkey:left", 'id': id});
        }
    }
});
