/**
 * This is the file which handles the socketIO connection for the agent view,
 * requesting a redraw of the grid when a socketIO update has been received.
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

    // specify a namespace, so that we only listen to messages from the server for this specific agent
    var namespace = "/agent";

    // make connection with the python server via a (web)socket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    /**
     * Event handler for new connections.
     */
    socket.on('connect', function() {
        console.log("Connected");

        var room = "/agent/" + id;

        // request to be added to room
        console.log("Requesting to be added to room:", room)
        socket.emit('join', {room: room});
    });

    /**
     * receive an update from the python server
     */
    socket.on('update', function(data){
        console.log("Received an update from the server:", data);

        if (!doVisualUpdates) {
            console.log("Chrome in background, skipping");
            return;
        }

        // unpack received data
        grid_size = data.params.grid_size;
        state = data.state;
        tick = data.params.tick;
        vis_bg_clr = data.params.vis_bg_clr;
        vis_bg_img = data.params.vis_bg_img;
        // draw the grid again
        requestAnimationFrame(function() {
            doTick(grid_size, state, tick, vis_bg_clr,vis_bg_img);
        });
    });

    /**
     * Stop the GUI drawing if we have been disconnected
     */
    socket.on('disconnect', function() {
        console.log('Got disconnected!');
        disconnected = true;
   });

});
