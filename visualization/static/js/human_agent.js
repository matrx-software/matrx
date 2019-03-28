// make connection with python server via socket
var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

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


// Catch userinput with arrow keys
// Arrows keys: up=1, right=2, down=3, left=4
document.onkeydown = checkArrowKey;
function checkArrowKey(e) {
    e = e || window.event;

    // filter for arrow keys (for now)
    if (e.keyCode < 37 || e.keyCode > 40) {
        return
    }

    // get ID which is saved in the HTML
    var id = document.getElementById('id').innerHTML;
    console.log("id:", id)

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
