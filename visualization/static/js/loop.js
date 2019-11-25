/**
 * In this file the loop is managed for requesting updates via the MATRXS API, and calling the draw functions for
 * updating the visualization.
 */

var initialized = false;
var tick_duration = 0.5;
var current_tick = 0;
var grid_size = [1, 1]
var rendered_update = true;
var open_update_request = false;
var first_tick = true;

// save the timestamp of our first tick, which we use to match the clock of MATRXS and the visualizer
var MATRXS_timestamp_start = null;
var vis_timestamp_start = null;
// ID of the world we received when initializing
var world_ID = null;
// ID of the world for which we received a tick, is it still the same as above or is this a new world?
var new_world_ID = null;
var restart_api = false;
var world_loop_stopped = false;

var msPerFrame = (1.0 / 60) * 1000; // placeholder
var tps = 1; // placeholder
var frames = 0;
var last_update = Date.now();
var timestamp = Date.now();

var init_url = 'http://127.0.0.1:3001/get_info'
var update_url = 'http://127.0.0.1:3001/get_latest_state/';
var send_userinput_url = 'http://127.0.0.1:3001/send_userinput/';
var agent_id = "";

// the latest MATRXS state
var state = {}

// how long to wait before sending a new request to MATRXS for a new state
var wait_for_next_tick = tick_duration;

/*
 * Once the page has loaded, call the initialization functions
 */
$(document).ready(function() {
    world_manager_loop();
});

function world_manager_loop() {
    init();

    // if the previous world ended, or we received a tick from a new world, reinitialize
    setInterval(function() {
        if (restart_api) {
            console.log("World ended, restarting world loop");
            init();
        }
    }, 500);
}

/*
 * Initialize the visualization
 */
function init() {
    console.log("Initializing..");

    world_loop_stopped = false;
    restart_api = false;

    // fetch the canvas element from the html
    initializeCanvas();

    // get the general MATRXS information to intialize the visualization
    var resp = initialConnect();

    // if we succesfully connected  to MATRXS, parse the general MATRXS info, preload the images and start the visualization
    resp.done(function(data) {
        parseInitialState(data);

        // add a hidden container to the html in which preloaded images can be added
        $('body').append("<div id='preloaded_imgs' style='display:none;'></div>");

        // preload the background
        preload_image(bgImage);

        // start the visualization loop
        world_loop();
    });

    // if the request gave an error, print to console and try again
    resp.fail(function(data) {
        console.log("Could not connect to MATRXS API, retrying in 0.5s");
        console.log(data);
        setTimeout(function() {
            init();
        }, 500);
    });

    console.log(">>>>>>>>>>>>>>>Init done<<<<<<<<<<<<<");
}

/*
 * Initialize the visualization by requesting the MATRXS scenario info.
 * If successful, the main visualization loop is called
 */
function initialConnect() {
    console.log("Fetching MATRXS initialization settings..");

    var path = window.location.pathname;
    // get the type ("" for god, "agent" or "human-agent") from the URL
    var type = path.substring(0, path.lastIndexOf('/'));
    if (type != "") {
        type = type.substring(1)
    };
    // Get the agent ID from the url (e.g. "god", "agent_0123", etc.)
    var ID = path.substring(path.lastIndexOf('/') + 1).toLowerCase();
    agent_id = ID;

    // check if this view is for the god view, agent, or human-agent, and get the correct urls
    if (type == "" && ID == "god") {
        console.log("This is the god view");
    } else if (type == "agent") {
        console.log("This view is for an Agent with ID:", agent_id);
    } else if (type == "human-agent") {
        console.log("This view is for a Human Agent with ID:", agent_id);
    }

    // fetch settings
    return jQuery.getJSON(init_url);
}

/*
 * Parse the initial MATRXS World state info
 */
function parseInitialState(data) {
    // on success, start the visualization loop
    initialized = true;
    tick_duration = data.tick_duration;
    world_ID = data.world_ID
    new_world_ID = null;

    current_tick = data.nr_ticks;
    grid_size = data.grid_shape;
    bgTileColour = data.vis_settings.visualization_bg_clr;
    bgImage = data.vis_settings.vis_bg_img;
    wait_for_next_tick = tick_duration * 1000;

    // calc ticks per second
    tps = Math.floor(1.0 / tick_duration);

    console.log("Fetched MATRXS settings:", data);
}


/*
 * The main visualization loop
 */
function world_loop() {
    timestamp = Date.now();
    var progress = 0;

    // Fetch an update from the server
    var to_update_or_not_to_update = Date.now() > last_update + wait_for_next_tick && !open_update_request;
    var update_request = false
    if (to_update_or_not_to_update) {
        // save that we requested an update at this time
        last_update = Date.now();
        open_update_request = true;
        update_request = get_MATRXS_update();
    }

    // we received an update for a new world, so reinitialize the visualization
    if (new_world_ID != null && world_ID != new_world_ID) {
        console.log("New world ID:", new_world_ID, "world_ID:", world_ID);
        first_tick = false;
        restart_api = true;
        return;
    }

    // if MATRXS didn't have a new tick yet, only redraw the current tick on screen
    if (!to_update_or_not_to_update) {
        draw()
        requestNewFrame();

    // if we requested an update check if it was successful
    } else {
        // after a successful update redraw the screen and go to the next frame
        update_request.done(function(data) {
            // the first tick, initialize the visualization with state information, and synch the timing between
            // the visualization and MATRXS
            if (first_tick) {
                populateMenu(state, agent_id);
                first_tick = false;
                // save the timestamp of our first tick, which we use to match the clock of MATRXS and the visualizer
                MATRXS_timestamp_start = curr_tick_timestamp;
                vis_timestamp_start = curr_tick_timestamp;
                console.log("MATRXs start:", MATRXS_timestamp_start, " vis start:", vis_timestamp_start);
            }

            open_update_request = false;
            draw(new_tick=true);
            requestNewFrame();
        })

        // if the request gave an error, print to console and try again after a delay (to prevent infinite loops)
        update_request.fail(function(data) {
            console.log("Could not connect to MATRXS API.");
            console.log("Provided error message:", data.responseJSON);
            console.log("Retrying in 0.5s");
            open_update_request = false;
            setTimeout(function() {
                requestNewFrame();
            }, 500);
        })
    }
}

function requestNewFrame() {

    // method 1
    window.requestAnimationFrame(world_loop);

    // method 2
//    var elapsed_time = Date.now() - timestamp;
//    var wait = msPerFrame - elapsed_time;
//    if ( wait < 0 ) {
//        wait = 0;
//    }
//    console.log("Elapsed time:", elapsed_time, " wait:", wait);

    // draw next frame in x milliseconds to achieve 60fps
//    setTimeout(world_loop, wait);
}


/*
 * Fetch an update from MATRXS when a new tick has occurred (based on tick duration speed)
 */
function get_MATRXS_update() {
    console.log("Fetching matrxs state with old wait:", wait_for_next_tick);

    // the get request is async, meaning the (success) function is only executed when
    // the response has been received
    var update_request = jQuery.getJSON(update_url + "['" + agent_id + "']", function(data) {
        console.log(data);
        state = data[data.length - 1][agent_id]['state'];

        var world_obj = state[0]['World'];
        var new_tick = state[0]['World']['nr_ticks'];
        curr_tick_timestamp = world_obj['curr_tick_timestamp'];
        tick_duration = world_obj['tick_duration'];
        tps = Math.floor(1.0 / tick_duration);

        // check what the ID of this world is. Is it still the same world we were expecting, or a new world?
        new_world_ID = world_obj['world_ID'];

        // Calculate the delay between when MATRXS sent the tick and the visualizer received the tick
        // This is calculated relative from the first time (from MATRXS and vis) onwards.
        var delay = (Date.now() - vis_timestamp_start) - (curr_tick_timestamp - MATRXS_timestamp_start);
        // calc how long we have to wait before fetching the next tick. This is calculated as
        // tick_duration - (delay) + a small buffer (15ms)
        wait_for_next_tick = tick_duration * 1000 - delay + 15;
        if (wait_for_next_tick <= 0) { wait_for_next_tick = tick_duration * 1000;}

        console.log("wait:", wait_for_next_tick, "tick dur:", tick_duration, "delay:", delay, " now js:", Date.now(), " MATRXS time:", curr_tick_timestamp);

        // the World object can be found at visualization depth 0
        bgTileColour = world_obj['vis_settings']['vis_bg_clr'];
        bgImage = world_obj['vis_settings']['vis_bg_img'];

        console.log("Current tick:", current_tick, " new_tick: ", new_tick)
        current_tick = new_tick;
    });
    return update_request;
}


/*
 * Send the object "data" to MATRXS as JSON data. The agent ID is automatically appended.
 */
function send_data_to_MATRXS(data) {
    // send an update for every key pressed
    var resp = $.ajax({
        method: "POST",
        url: send_userinput_url + agent_id,
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        data: JSON.stringify(data),
        success: function() {
            //console.log("Data sent to MATRXS");
        },
    });
    return resp;
}
