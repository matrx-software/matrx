/**
 * This is the file which handles the socketIO connection for the god view,
 * requesting a redraw of the grid when a socketIO update has been received.
 */

var doVisualUpdates = true;
// var isFirstCall=true;

/**
 * Check if the current tab is in focus or not
 */
document.addEventListener('visibilitychange', function() {
    doVisualUpdates = !document.hidden;
});


var initialized = false;
var tick_duration = 0.5;
var current_tick = 0;
var rendered_update = true;

var frames = 0;

var lastRender = 0;
var last_update = 0;

var init_url = 'http://localhost:3000/get_info'
var update_url = 'http://localhost:3000/get_god_state/'



/*
 * Update the state of the world for the elapsed time since last render
 */
function update(progress) {
    console.log("Update with progress:", progress)

    // check if there is a new tick available yet based on the tick_duration
    if ((new Date()).getTime() > last_update + (tick_duration * 1000) ) {
        get_MATRXS_update();
    }

    console.log("Updating object locations etc.");
}

/*
 * Draw all objects on the canvas
 */
function draw() {
    // Draw the state of the world
    console.log("drawing the world, frame:", frames);
    frames++;
}

/*
 * The main visualization loop
 */
function loop() {
    var timestamp = (new Date()).getTime();
    var progress = timestamp - lastRender

    update(progress)
    draw()

    lastRender = timestamp
    window.requestAnimationFrame(loop)
}


/*
 * Fetch an update from MATRXS, based on tick duration speed
 */
function get_MATRXS_update() {
    console.log("Fetching update..");

    // the get request is async, meaning the function is only executed when
    // the response has been received
    jQuery.getJSON(update_url + current_tick, function(data) {
        rendered_changes = false;
        last_update = (new Date()).getTime();
        console.log("Fetched update, received data:", data)

        current_tick = data[data.length-1]['god']['state']['World']['nr_ticks'];
        console.log("Latest tick set to:", current_tick);
    });
}



/*
 * Initialize the visualization by requesting the MATRXS scenario info.
 * If succesful, the main visualization loop is called
 */
function init() {
    console.log("initializing")

    // fetch settings
    var resp = jQuery.getJSON(init_url, function(data) {
        initialized = true;
        tick_duration = data.tick_duration;
        current_tick = data.tick;
        console.log("MATRXS settings:", data);

        // start the visualization loop
        loop();
    });

    // if the request gave an error, print to console and try again
    resp.fail(function() {
        console.log("could not fetch MATRXS information, retrying in 0.5s");
        setTimeout(function(){
            init();
        }, 500);
    })

}


$(document).ready(function() {
    init();
});



//
//    /**
//     * receive an update from the python server
//     */
//    socket.on('update', function(data){
//         console.log("Received an update from the server:", data);
//
//        // Only perform the GUI update if it is in the foreground, as the
//        // background tabs are often throttled after which the browser cannot
//        // keepup
//        if (!doVisualUpdates) {
//            console.log("Chrome in background, skipping");
//            return;
//        }
//
//        // unpack received data
//        grid_size = data.params.grid_size;
//        state = data.state;
//        tick = data.params.tick;
//        vis_bg_clr = data.params.vis_bg_clr;
//        vis_bg_img = data.params.vis_bg_img;
//        //draw the menu if it is the first call
//        if(isFirstCall){
//            isFirstCall=false;
//            populateMenu(state);
//            parseGifs(state);}
//        // draw the grid again
//        requestAnimationFrame(function() {
//            doTick(grid_size, state, tick, vis_bg_clr,vis_bg_img, parsedGifs);
//        });
//    });
