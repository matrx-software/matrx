$(document).ready(function(){

    // specify a namespace, so that we only listen to messages from the server for this specific human agent
    var namespace = "/human-agent/" + document.getElementById('id').innerHTML;

    // make connection with python server via socket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    // Event handler for new connections.
    socket.on('connect', function() {
        console.log("Connected");
    });

    // receive an update from the python server
    socket.on('update', function(data){
        console.log("Received an update from the server:", data);

        // unpack received data
        grid_size = data.params.grid_size;
        state = data.state;

        // draw the grid again
        requestAnimationFrame(function() {
            drawSim(grid_size, state);
        });
    });

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
            socket.emit("userinput", {"movement": 1, 'id': id});
        }
        else if (e.keyCode == '39') {
           // right arrow
           socket.emit("userinput", {"movement": 2, 'id': id});
        }
        else if (e.keyCode == '40') {
            // down arrow
            socket.emit("userinput", {"movement": 3, 'id': id});
        }
        else if (e.keyCode == '37') {
           // left arrow
           socket.emit("userinput", {"movement": 4, 'id': id});
        }
    }
});
