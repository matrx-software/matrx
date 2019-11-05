/**
 * This is the file which handles the socketIO connection for the god view,
 * requesting a redraw of the grid when a socketIO update has been received.
 */

var initialized = false;
var tick_duration = 0.5;
var current_tick = 0;
var grid_size = [1,1]
var rendered_update = true;
var open_update_request = false;

var msPerFrame = (1.0 / 60) * 1000; // placeholder
var tps = 1; // placeholder
var frames = 0;
var lastRender = 0;
var last_update = (new Date()).getTime();

var init_url = 'http://127.0.0.1:3001/get_info'
var update_url = 'http://127.0.0.1:3001/get_latest_state/';

var state = {}

/*
 * Update the state of the world for the elapsed time since last render
 */
function update(progress) {

    // check if there is a new tick available yet based on the tick_duration
    if ((new Date()).getTime() > last_update + (tick_duration * 1000) && !open_update_request) {
        // save that we requested an update at this time
        last_update = (new Date()).getTime();
        open_update_request = true;
        return get_MATRXS_update();
    }

    return false;
}


/*
 * The main visualization loop
 */
function loop() {
    var timestamp = (new Date()).getTime();
    var progress = timestamp - lastRender;
    lastRender = timestamp;
//    console.log("Last frame took:", progress , " while it should take:", msPerFrame);

//     Fetch an update from the server
    var update_request = update(progress);

    // if we didn't get an update yet, redraw the screen
    if (! update_request) {
        draw()
        window.requestAnimationFrame(loop)

    // if we requested an update check if it was successful
    } else {
        // after a successful update redraw the screen and go to the next frame
        update_request.done(function(data) {
//            console.log("update was successful, drawing and requesting a new animation frame");
            draw(new_tick=true);
            lastRender = timestamp
            window.requestAnimationFrame(loop)
        })

        // if the request gave an error, print to console and try again after a delay (to prevent infinite loops)
        update_request.fail(function() {
            console.log("Could not connect to MATRXS API, retrying in 0.5s");
            setTimeout(function(){
                lastRender = timestamp
                window.requestAnimationFrame(loop)
            }, 500);
        })
    }
}

/*
 * Fetch an update from MATRXS when a new tick has occurred (based on tick duration speed)
 */
function get_MATRXS_update() {
    var a = performance.now();
    // the get request is async, meaning the function is only executed when
    // the response has been received

    var update_request = $.ajax({
        method: 'GET',
        url: update_url + "['god']",
        dataType: "json",
        success: function(data) {
            open_update_request = false;
            state = data[data.length-1]['god']['state']
            current_tick = data[data.length-1]['god']['tick'];
        }
    });

    return update_request;
}



/*
 * Initialize the visualization by requesting the MATRXS scenario info.
 * If successful, the main visualization loop is called
 */
function init() {
    console.log("initializing")

    var a = performance.now();
    // fetch settings
    var resp = jQuery.getJSON(init_url, function(data) {
        initialized = true;
        tick_duration = data.tick_duration;
        current_tick = data.tick;
        grid_size = data.grid_size;

        console.log("Fetched initial MATRXS update in ", performance.now() - a, "ms");
        console.log("MATRXS settings:", data);

        // start the visualization loop
        loop();
    });

    // if the request gave an error, print to console and try again
    resp.fail(function() {
        console.log("Could not connect to MATRXS API, retrying in 0.5s");
        setTimeout(function(){
            init();
        }, 500);
    });


}

/**
 * Draw all objects on the canvas
 * @param new_tick = whether this is the first draw after a new tick/update
 */
function draw(new_tick) {
    // for the first time drawing the visualization, calculate the optimal
    // screen size based on the grid size
    if (firstDraw) {
        isFirstCall=false;
        populateMenu(state);
        parseGifs(state);


        console.log("First draw, resetting canvas and tile sizes");
        fixCanvasSize();
        firstDraw = false;
        updateGridSize(grid_size); // save the number of cells in x and y direction of the map
        // calc ticks per second
        tps = Math.floor(1.0 / tick_duration);
    }

    // calculate how many milliseconds 1 frame should take based on our framerate last second
    msPerFrame = (1.0 / framesLastSecond) * 1000;

    if (new_tick) {
        // the tracked objects from last iteration are moved to a separate list
        prevAnimatedObjects = animatedObjects;
        animatedObjects = {};
    }

    // Draw the state of the world
    frames++;

    calcFps();
    updateGridSize(grid_size); // save the number of cells in x and y direction of the map
    drawBg(); // draw a default bg tile

    // identify the objects we received
    var obj_keys = Object.keys(state);

    // calculate how many frames the animation of movement should take
    var animationDurationFrames = (framesLastSecond / tps) * animationDurationPerc;

    // calculate how many milliseconds the movement animation should take
    var animationDurationMs = animationDurationFrames * msPerFrame;

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
    ctx.fillText("TPS: " + tps, 65, 20);

}


$(document).ready(function() {
    init();
});