var doVisualUpdates = true;

/**
 * Check if the current tab is in focus or not
 */
document.addEventListener('visibilitychange', function(){
  doVisualUpdates = !document.hidden;
});

$(document).ready(function(){
    // specify a namespace, so that we only listen to messages from the server for the god view
    var namespace = "/god"

    // make connection with python server via socket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    /**
     * Event handler for new connections.
     */
    socket.on('connect', function() {
        console.log("Connected");
    });

    /**
     * receive an update from the python server
     */
    socket.on('update', function(data){
        // console.log("Received an update from the server:", data);

        // Only perform the GUI update if it is in the foreground, as the
        // background tabs are often throttled after which the browser cannot
        // keepup
        if (!doVisualUpdates) {
            console.log("Chrome in background, skipping");
            return;
        }

        // unpack received data
        grid_size = data.params.grid_size;
        state = data.state;
        tick = data.params.tick;


        // draw the grid again
        requestAnimationFrame(function() {
            doTick(grid_size, state, tick);
        });
    });
});
