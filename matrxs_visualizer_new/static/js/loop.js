/**
 * In this file the loop is managed for requesting updates via the MATRXS API, and calling the draw functions for
 * updating the visualization.
 *
 * As this file has access to the gen_grid.js file variables, all variables are prefixed with lv_ (loop variable)
 * such that no variables are accidently created in both files, leading to unexpected behaviours.
 */



// vars that will be passed to the visualizer file
var lv_state = {}, // the latest MATRXS state
    lv_world_settings = null;

var lv_tick_duration = 0.5,
    lv_current_tick = 0,
    lv_grid_size_loop = [1, 1],
    lv_open_update_request = false, // whether a new request to MATRXS is pending right now
    lv_first_tick = true;

// save the timestamp of our first tick, which we use to match the clock of MATRXS and the visualizer
var lv_MATRXS_timestamp_start = null,
    lv_vis_timestamp_start = null,
    lv_world_ID = null, // ID of the world we received when initializing
    lv_new_world_ID = null, // ID of the world for which we received a tick
    lv_reinitialize_vis = false, // whether to reinitialize the visualization
    lv_wait_for_next_tick = 0, // how long to wait before sending a new request to MATRXS for a new state
    lv_matrxs_paused = false;

var lv_tps = 1, // placeholder value
    lv_msPerFrame = (1.0 / 60) * 1000, // placeholder
    lv_last_update = Date.now(), // timestamp of last MATRXS state update
    lv_timestamp = Date.now();

// MATRXS API urls
var lv_base_url = window.location.hostname,
    lv_init_url = 'http://' + lv_base_url + ':3001/get_info',
    lv_update_url = 'http://' + lv_base_url + ':3001/get_latest_state/',
    lv_send_userinput_url = 'http://' + lv_base_url + ':3001/send_userinput/',
    lv_agent_id = "";


console.log("lv_send_userinput_url:", lv_send_userinput_url);

/*
 * Once the page has loaded, call the initialization functions
 */
$(document).ready(function() {
    world_manager_loop();
});

/* The loop which keeps the visualizer running, even if MATRXS worlds are stopped / restarted / switched */
function world_manager_loop() {
    init();

    // if the previous world ended or we had issues in initializing the world, reinitialize
    setInterval(function() {
        if (lv_reinitialize_vis) {
            init();
        }
    }, 500);
}

/*
 * Initialize the visualization
 */
function init() {
    console.log("Initializing..");

    // init a number of vis variables
    lv_reinitialize_vis = false;
    lv_open_update_request = false;

    // fetch the canvas element from the html
    initialize_grid();

    // get the general MATRXS information to intialize the visualization
    var resp = initial_connect();

    // if we succesfully connected to MATRXS, parse the general MATRXS info, preload the images and start the visualization
    resp.done(function(data) {
        // check if the init data actually contains anything, if not MATRXS may still be starting up and we need to retry
        if (Object.entries(data).length === 0 && data.constructor === Object) {
            lv_reinitialize_vis = true;
            return;
        }
        parse_initial_state(data);

        // add a hidden container to the html in which preloaded images can be added
        $('body').append("<div id='preloaded_imgs' style='display:none;'></div>");

        // if MATRXS is running, change the start/pause button to match that
        sync_play_button(lv_matrxs_paused);

        // preload the background image
//        preload_image(bgImage);

        // start the visualization loop
        world_loop();

    });

    // if the request gave an error, print to console and try again
    resp.fail(function(data) {
        console.log("Could not connect to MATRXS API, retrying in 0.5s");
        lv_reinitialize_vis = true;
        return;
    });

}

/*
 * Initialize the visualization by requesting the MATRXS scenario info.
 * If successful, the main visualization loop is called
 */
function initial_connect() {
    console.log("Fetching MATRXS initialization settings..");

    var lv_path = window.location.pathname;
    // get the view type ("" for god, "agent" or "human-agent") from the URL
    var lv_type = lv_path.substring(0, lv_path.lastIndexOf('/'));
    if (lv_type != "") {
        lv_type = lv_type.substring(1)
    };
    // Get the agent ID from the url (e.g. "god", "agent_0123", etc.)
    var lv_ID = lv_path.substring(lv_path.lastIndexOf('/') + 1).toLowerCase();
    // decode the URL (e.g. spaces are encoding in urls as %20), and set the agent ID
    lv_agent_id = decodeURI(lv_ID);


    // check if this view is for the god view, agent, or human-agent, and get the correct urls
    if (lv_type == "" && lv_ID == "god") {
        console.log("This is the god view");
    } else if (lv_type == "agent") {
        console.log("This view is for an Agent with ID:", lv_agent_id);
    } else if (lv_type == "human-agent") {
        console.log("This view is for a Human Agent with ID:", lv_agent_id);
    }

    // fetch settings
    return jQuery.getJSON(lv_init_url);
}

/*
 * Parse the initial MATRXS World state info
 */
function parse_initial_state(data) {
    console.log("Fetched MATRXS settings:", data);

    // on success, parse the setup variables
    lv_tick_duration = data.tick_duration;
    lv_world_ID = data.world_ID
    lv_new_world_ID = null;
    lv_current_tick = data.nr_ticks;
    lv_grid_size_loop = data.grid_shape;
    lv_wait_for_next_tick = 0;
    lv_tps = Math.floor(1.0 / lv_tick_duration); // calc ticks per second
    lv_matrxs_paused = data.matrxs_paused;
}


/*
 * The visualization loop for a MATRXS world
 */
function world_loop() {
    lv_timestamp = Date.now();

    // Check if we need to fetch an update from MATRXS
    var lv_to_update_or_not_to_update = Date.now() > lv_last_update + lv_wait_for_next_tick && !lv_open_update_request;
    var lv_update_request = false
    // request a MATRXS state update
    if (lv_to_update_or_not_to_update) {
        // save that we requested an update at this time
        lv_last_update = Date.now();
        lv_open_update_request = true;
        lv_update_request = get_MATRXS_update();
    }

    // we received an update for a different world from our current, so reinitialize the visualization
    if (lv_new_world_ID != null && lv_world_ID != lv_new_world_ID) {
        console.log("New world ID received:", lv_new_world_ID);
        lv_first_tick = false;
        lv_reinitialize_vis = true;
        sync_play_button();
        return;
    }

    // if MATRXS didn't have a state update yet, wait for the next frame and check again at that time
    if (!lv_to_update_or_not_to_update) {
        request_new_frame();

    // if we requested an update check if it was successful
    } else {
        // after a successful update redraw the screen and go to the next frame
        lv_update_request.done(function(data) {

            // the first tick, initialize the visualization with state information, and synch the timing between
            // the visualization and MATRXS
            if (lv_first_tick) {
                lv_first_tick = false;
                // save the timestamp of our first tick, which we use to match the clock of MATRXS and the visualizer
                lv_MATRXS_timestamp_start = curr_tick_timestamp;
                lv_vis_timestamp_start = curr_tick_timestamp;
            }

            // redraw the screen and go to the next frame
            lv_open_update_request = false;
            draw(lv_state, lv_world_settings, new_tick=true);
            request_new_frame();
        })

        // if the request gave an error, print to console and try to reinitialize
        lv_update_request.fail(function(data) {
//        lv_update_request.fail(function(jqxhr, textStatus, error) {
//            var err = textStatus + ", " + error;
//            console.log( "Error: " + err );

            console.log("Could not connect to MATRXS API.");
            console.log("Provided error:", data.responseJSON)
            lv_first_tick = false;
            lv_reinitialize_vis = true;
            return;
        });
    }
}

function request_new_frame() {

    // method 1
    window.requestAnimationFrame(world_loop);

    // method 2
//    var elapsed_time = Date.now() - lv_timestamp;
//    var wait = lv_msPerFrame - elapsed_time;
//    if ( wait < 0 ) {
//        wait = 0;
//    }
//    console.log("Elapsed time:", elapsed_time, " wait:", wait);

    // draw next frame in x milliseconds to achieve 60fps
//    setTimeout(world_loop, wait);
}


/*
 * Fetch an update from the MATRXS API
 */
function get_MATRXS_update() {
    // console.log("Fetching matrxs state with old wait:", lv_wait_for_next_tick);

    // the get request is async, meaning the (success) function is only executed when
    // the response has been received
    var lv_update_request = jQuery.getJSON(lv_update_url + "['" + lv_agent_id + "']", function(data) {

        // decode lv_state and other info from the request
        lv_state = data[data.length - 1][lv_agent_id]['state'];
        var lv_new_tick = lv_state['World']['nr_ticks'];
        curr_tick_timestamp = lv_state['World']['curr_tick_timestamp'];
        lv_tick_duration = lv_state['World']['tick_duration'];
        lv_tps = (1.0 / lv_tick_duration).toFixed(1); // round to 1 decimal behind the dot

        lv_world_settings = lv_state['World'];

        // check what the ID of this world is. Is it still the same world we were expecting, or a different world?
        lv_new_world_ID = lv_state['World']['world_ID'];

        // Calculate the delay between when MATRXS sent the tick and the visualizer received the tick
        // The calculation takes a (potential) difference in time between MATRXS and the visualizer into account
        var lv_delay = (Date.now() - lv_vis_timestamp_start) - (curr_tick_timestamp - lv_MATRXS_timestamp_start);

        // calc how long we have to wait before fetching the next tick. This is calculated as
        // tick_duration - delay + a small buffer (15ms)
        lv_wait_for_next_tick = lv_tick_duration * 1000 - lv_delay + 15;
        if (lv_wait_for_next_tick <= 0) { lv_wait_for_next_tick = lv_tick_duration * 1000;}

        // note our new current tick
        lv_current_tick = lv_new_tick;

        // make sure to synchronize the play/pause button of the frontend with the current MATRX version
        var matrxs_paused = lv_state['World']['matrxs_paused'];
        if (matrxs_paused != lv_matrxs_paused) {
            lv_matrxs_paused = matrxs_paused;
            sync_play_button(lv_matrxs_paused);
        }
    });
    return lv_update_request;
}


/*
 * Send the object "data" to MATRXS as JSON data. The agent ID is automatically appended.
 */
function send_data_to_MATRXS(data) {
    // send an update for every key pressed
    var lv_resp = $.ajax({
        method: "POST",
        url: lv_send_userinput_url + lv_agent_id,
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        data: JSON.stringify(data),
        success: function() {
            //console.log("Data sent to MATRXS");
        },
    });
    return lv_resp;
}
