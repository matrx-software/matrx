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
var grid_size = [1,1]
var rendered_update = true;

var frames = 0;
var lastRender = 0;
var last_update = 0;

var init_url = 'http://localhost:3000/get_info'
var update_url = 'http://localhost:3000/get_god_state/'

var state = {}

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

    // for the first time drawing the visualization, calculate the optimal
    // screen size based on the grid size
    if (firstDraw) {
        console.log("First draw, resetting canvas and tile sizes");
        fixCanvasSize();
        firstDraw = false;
        // bgTileColour = vis_bg_clr;
        // bgImage = vis_bg_img;
        bgImage = null;
        bgTileColour = "#ffffff";
    }

}


/*
 * The main visualization loop
 */
function loop() {
    var timestamp = (new Date()).getTime();
    var progress = timestamp - lastRender

    update(progress)
    // drawSim(grid_size, state, curr_tick, false);
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
        state = data[data.length-1]['god']
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
        grid_size = data.grid_size;

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






/**
 * called when a new tick is received by the agent
 */
// function doTick(state, curr_tick, vis_bg_clr=None, vis_bg_img=None) {
//     // for the first time drawing the visualization, calculate the optimal
//     // screen size based on the grid size
//     if (firstDraw) {
//         // console.log("First draw, resetting canvas and tile sizes");
//         fixCanvasSize();
//         firstDraw = false;
//         bgTileColour = vis_bg_clr;
//         bgImage = vis_bg_img;
//     }
//
//     // console.log("\n#####################################\nNew tick #", curr_tick);
//
//     // calc the ticks per second
//     highestTickSoFar = curr_tick;
//     lastTickSecond = Date.now();
//     calc_tps();
//     // the tracked objects from last iteration are moved to a seperate list
//     prevAnimatedObjects = animatedObjects;
//     animatedObjects = {};
//
//     // console.log("Received state:", state);
//
//     // if we have less than X ticks per second (by default 60), animate the movement
//     if (ticksLastSecond < targetFPS && ticksLastSecond > 0) {
//         drawSim(grid_size, state, curr_tick, true);
//     } else {
//         drawSim(grid_size, state, curr_tick, false);
//     }
// }


/**
* Draw all objects on the canvas
 */
function draw(grid_size, state, curr_tick, animateMovement) {

    // Draw the state of the world
    console.log("drawing the world, frame:", frames);
    frames++;

    // return in the case that the canvas has disappeared
    // if (ctx == null) {
    //     return;
    // }

    // console.log("Tick:", curr_tick, "highest tick:", highestTickSoFar);

    // return in case there is a new tick, and we are still updating the old tick
    // if (curr_tick != highestTickSoFar) {
    //     // console.log("Updating old tick, return");
    //     return;
    // }
    // console.log("Drawing grid");



    calc_fps();
    updateGridSize(grid_size); // save the number of cells in x and y direction of the map
    drawBg(); // draw a default bg tile

    // identify the objects we received
    var obj_keys = Object.keys(state);

    // calculate a number of necessary variables for timing the movement animation
    // how many milliseconds should 1 frame take
    var msPerFrame = (1.0 / targetFPS) * 1000;

    // how many frames should the animation of movement take
    var animationDurationFrames = (targetFPS / ticksLastSecond) * animationDurationPerc;

    // how many milliseconds the animation of movement should take
    var animationDurationMs = animationDurationFrames * msPerFrame;

    // console.log("Animated objects:", animatedObjects);

    // Loop through the visualization depths
    var vis_depths = Object.keys(state);
    vis_depths.forEach(function(vis_depth) {

        // Loop through the objects at this depth and visualize them
        var objects = Object.keys(state[vis_depth]);
        objects.forEach(function(objID) {

            // fetch object
            obj = state[vis_depth][objID]

            // fetch location of object in pixel values
            var x = obj['location'][0] * px_per_cell;
            var y = obj['location'][1] * px_per_cell;

            // keep track of objects which need to be animated

            // fetch the previous location of the object from last iteration
            if (!(objID in animatedObjects) && objID in prevAnimatedObjects) {
                // console.log("Fetching", objID, " from prevAnimatedObjects");
                animatedObjects[objID] = {
                    "loc_from": prevAnimatedObjects[objID]["loc_to"],
                    "loc_to": obj['location'],
                    "position": cellsToPxs(prevAnimatedObjects[objID]["loc_to"]),
                    "timeStarted": Date.now()
                };
            }

            // check if we need to animate this movement, which is the case if:
            // it it is our first encounter with this object, or it moves to a new position
            if (!(objID in animatedObjects && animatedObjects[objID]['loc_from'] == obj['location'])) {
                // console.log("This is a moving agent", obj);
                // console.log("From ", obj["prev_location"][0], obj["prev_location"][1], "(",cellsToPxs(obj["prev_location"])[0], cellsToPxs(obj["prev_location"])[1], ") to", obj["location"][0], obj["location"][1], "(",cellsToPxs(obj["location"])[0], cellsToPxs(obj["location"])[1], ")");
                var pos = processMovement(objID, obj['location'], animatedObjects, animationDurationMs);
                // round the location to round pixel values
                x = Math.round(pos[0]);
                y = Math.round(pos[1]);
                // console.log("Agent new coordinates:", x, y);
            }

            // get the object  size
            sz = obj['visualization']['size'];
            // get and convert the colour from hex to rgba
            clr = obj['visualization']['colour'];
            opacity = obj['visualization']['opacity'];
            clr = hexToRgba(clr, opacity);

            // draw the object with the correct shape, size and colour
            if (obj['visualization']['shape'] == 0) {
                drawRectangle(x, y, px_per_cell, px_per_cell, clr, sz)
            } else if (obj['visualization']['shape'] == 1) {
                drawTriangle(x, y, px_per_cell, px_per_cell, clr, sz);
            } else if (obj['visualization']['shape'] == 2) {
                drawCircle(x, y, px_per_cell, px_per_cell, clr, sz);
            } else if (obj['visualization']['shape'] == 'img') {
                drawImage(obj['img_name'], x, y, px_per_cell, px_per_cell, sz);
            }
        })
    });

    // Draw the FPS to the canvas as last so it's drawn on top
    ctx.fillStyle = "#ff0000";
    ctx.fillText("FPS: " + framesLastSecond, 10, 20);
    ctx.fillText("TPS: " + ticksLastSecond, 65, 20);

    // if (animateMovement) {
    //     // console.log("Calling draw recursively at:", Date.now(), " with delay in ms: ", msPerFrame);
    //
    //     // call the draw function again after a short sleep to get to desired number of fps in milliseconds
    //     setTimeout(function() {
    //         drawSim(grid_size, state, curr_tick, animateMovement);
    //     }, msPerFrame);
    // }
}
