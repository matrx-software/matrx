/**
 * This is the file which handles the socketIO connection for the human agent view,
 * requesting a redraw of the grid when a socketIO update has been received.
 * Specific to the human agent, key inputs are also handled and sent back to the server.
 */

var doVisualUpdates = true;

/**
 * Check if the current tab is in focus or not
 */
document.addEventListener('visibilitychange', function(){
  doVisualUpdates = !document.hidden;
});

$(document).ready(function(){

    var id = document.getElementById('id').innerHTML;

    // specify a namespace, so that we only listen to messages from the server for this specific human agent
    var namespace = "/humanagent";

    // make connection with python server via socket to get messages only for the human agent
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    /**
     * Event handler for new connections.
     */
    socket.on('connect', function() {
        console.log("Connected");

        var room = "/humanagent/" + id;

        // request to be added to room so the server can send messages specific to this human agent
        console.log("Requesting to be added to room:", room)
        socket.emit('join', {room: room});
    });

    /**
     * receive an update from the python server
     */
    socket.on('update', function(data){
        if (!doVisualUpdates) {
            console.log("Chrome in background, skipping");
            return;
        }

        // unpack received data
        grid_size = data.params.grid_size;
        state = data.state;
        tick = data.params.tick;
        vis_bg_clr = data.params.vis_bg_clr;

        // draw the grid again
        requestAnimationFrame(function() {
            doTick(grid_size, state, tick, vis_bg_clr);
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

        // send an update for every key pressed
        socket.emit("userinput", {"key": e.key, 'id': id});
    }
});
