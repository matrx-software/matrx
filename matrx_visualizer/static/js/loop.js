/**
 * In this file the loop is managed for requesting updates via the MATRX API, and calling the draw functions for
 * updating the visualization.
 *
 * As this file has access to the gen_grid.js file variables, all variables are prefixed with lv_ (loop variable)
 * such that no variables are accidently created in both files, leading to unexpected behaviours.
 */



// vars that will be passed to the visualizer file
var lv_state = {}, // the latest MATRX state
    lv_world_settings = null,
    lv_messages = null, // the messages received by the current agent of the current tick
    lv_chatrooms = null; // the accessible chatrooms for the current agent

var lv_tick_duration = 0.5,
    lv_current_tick = 0,
    lv_grid_size_loop = [1, 1],
    lv_open_update_request = false, // whether a new request to MATRX is pending right now
    lv_first_tick = true;

// save the timestamp of our first tick, which we use to match the clock of MATRX and the visualizer
var lv_world_ID = null, // ID of the world we received when initializing
    lv_new_world_ID = null, // ID of the world for which we received a tick
    lv_reinitialize_vis = false, // whether to reinitialize the visualization
    lv_wait_for_next_tick = 0, // how long to wait before sending a new request to MATRX for a new state
    lv_matrx_paused = false,
    lv_fps = 0,
    lv_this_second = null,
    lv_frames_this_second = null;

var lv_tps = 1, // placeholder value
    lv_msPerFrame = (1.0 / 60) * 1000, // placeholder
    lv_last_update = Date.now(), // timestamp of last MATRX state update
    lv_timestamp = Date.now();

// MATRX API urls
var lv_base_url = window.location.hostname,
    lv_init_url = 'http://' + lv_base_url + ':3001/get_info',
    lv_update_url = 'http://' + lv_base_url + ':3001/get_latest_state_and_messages/',
    lv_send_userinput_url = 'http://' + lv_base_url + ':3001/send_userinput/',
    lv_agent_id = "",
    lv_agent_type = null;

// check if message offsets are defined and used in gen_grid.js
if (typeof chat_offsets !== 'undefined') {
    var chat_offsets = {};
}


console.log("lv_send_userinput_url:", lv_send_userinput_url);

/*
 * Once the page has loaded, call the initialization functions
 */
$(document).ready(function() {
    world_manager_loop();
});

/* The loop which keeps the visualizer running, even if MATRX worlds are stopped / restarted / switched */
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

    // get the general MATRX information to intialize the visualization
    var resp = initial_connect();

    // if we succesfully connected to MATRX, parse the general MATRX info, preload the images and start the visualization
    resp.done(function(data) {
        // check if the init data actually contains anything, if not MATRX may still be starting up and we need to retry
        if (Object.entries(data).length === 0 && data.constructor === Object) {
            lv_reinitialize_vis = true;
            return;
        }
        parse_initial_state(data);

        // add a hidden container to the html in which preloaded images can be added
        $('body').append("<div id='preloaded_imgs' style='display:none;'></div>");

        // if MATRX is running, change the start/pause button to match that
        sync_play_button(lv_matrx_paused);

        // start the visualization loop
        world_loop();
    });

    // if the request gave an error, print to console and try again
    resp.fail(function(data) {
        console.log("Could not connect to MATRX API, retrying in 0.5s");
        lv_reinitialize_vis = true;
        return;
    });

}

/*
 * Initialize the visualization by requesting the MATRX scenario info.
 * If successful, the main visualization loop is called
 */
function initial_connect() {
    console.log("Fetching MATRX initialization settings..");

    var lv_path = window.location.pathname;
    // get the view type ("" for god, "agent" or "human-agent") from the URL
    lv_agent_type = lv_path.substring(0, lv_path.lastIndexOf('/'));
    if (lv_agent_type != "") {
        lv_agent_type = lv_agent_type.substring(1)
    };
    // Get the agent ID from the url (e.g. "god", "agent_0123", etc.)
    var lv_ID = lv_path.substring(lv_path.lastIndexOf('/') + 1).toLowerCase();
    // decode the URL (e.g. spaces are encoding in urls as %20), and set the agent ID
    lv_agent_id = decodeURI(lv_ID);


    // check if this view is for the god view, agent, or human-agent, and get the correct urls
    if (lv_agent_type == "" && lv_ID == "god") {
        lv_agent_type = "god";
        console.log("This is the god view");
    } else if (lv_agent_type == "agent") {
        console.log("This view is for an Agent with ID:", lv_agent_id);
    } else if (lv_agent_type == "human-agent") {
        console.log("This view is for a Human Agent with ID:", lv_agent_id);
    }

    // fetch settings
    return jQuery.getJSON(lv_init_url);
}

/*
 * Parse the initial MATRX World state info
 */
function parse_initial_state(data) {
    console.log("Fetched MATRX settings:", data);

    // on success, parse the setup variables
    lv_tick_duration = data.tick_duration;
    lv_world_ID = data.world_ID
    lv_new_world_ID = null;
    lv_current_tick = data.nr_ticks;
    lv_init_tick = lv_current_tick;
    lv_grid_size_loop = data.grid_shape;
    lv_wait_for_next_tick = 0;
    lv_tps = Math.floor(1.0 / lv_tick_duration); // calc ticks per second
    lv_matrx_paused = data.matrx_paused;
}


/*
 * The visualization loop for a MATRX world
 */
function world_loop() {
    lv_timestamp = Date.now();

    // keep track of number of frames per second
    if (lv_this_second == null) {
        lv_this_second = Date.now();
    } else if( (Date.now() - lv_this_second) > 1000) {
        lv_fps = lv_frames_this_second;
//        console.log("Fps: ", lv_fps);
        lv_frames_this_second = 0;
        lv_this_second = Date.now();
    } else {
        lv_frames_this_second++;
    }

    // Check if we need to fetch an update from MATRX
    var lv_to_update_or_not_to_update = Date.now() > lv_last_update + lv_wait_for_next_tick && !lv_open_update_request;
    var lv_update_request = false
    // request a MATRX state update
    if (lv_to_update_or_not_to_update) {
        // save that we requested an update at this time
        lv_last_update = Date.now();
        lv_open_update_request = true;
        lv_update_request = get_MATRX_update();
    }

    // we received an update for a different world from our current, so reinitialize the visualization
    if (lv_new_world_ID != null && lv_world_ID != lv_new_world_ID) {
        console.log("New world ID received:", lv_new_world_ID);
        lv_first_tick = false;
        lv_reinitialize_vis = true;
        sync_play_button(lv_matrx_paused);
        return;
    }

    // if MATRX didn't have a state update yet, wait for the next frame and check again at that time
    if (!lv_to_update_or_not_to_update) {
        request_new_frame();

    // if we requested an update check if it was successful
    } else {
        // after a successful update redraw the screen and go to the next frame
        lv_update_request.done(function(data) {

            // the first tick, initialize the visualization with state information, and synch the timing between
            // the visualization and MATRX
            if (lv_first_tick) {
                lv_first_tick = false;
            }

            // redraw the screen and go to the next frame
            lv_open_update_request = false;
            draw(lv_state, lv_world_settings, lv_messages, lv_chatrooms, new_tick = true);
            request_new_frame();
        })

        // if the request gave an error, print to console and try to reinitialize
        lv_update_request.fail(function(data) {
            //        lv_update_request.fail(function(jqxhr, textStatus, error) {
            //            var err = textStatus + ", " + error;
            //            console.log( "Error: " + err );

            console.log("Could not connect to MATRX API.");
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
 * Fetch an update from the MATRX API
 */
function get_MATRX_update() {
    // console.log("Fetching matrx state with old wait:", lv_wait_for_next_tick);

    data = {"agent_id": lv_agent_id, "chat_offsets": chat_offsets};

    // the request is async, meaning the (success) function is only executed when
    // the response has been received
    var lv_update_request = $.ajax({
        method: "POST",
        url: lv_update_url,
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        data: JSON.stringify(data),
        success: function(data) {
            //        console.log("Received update request:", lv_update_request);
            lv_messages = data.messages;
            lv_chatrooms = data.chatrooms;

            // decode lv_state and other info from the request
            lv_state = data['states'][data['states'].length - 1][lv_agent_id]['state'];
            var lv_new_tick = lv_state['World']['nr_ticks'];
            curr_tick_timestamp = lv_state['World']['curr_tick_timestamp'];
            lv_tick_duration = lv_state['World']['tick_duration'];
            lv_tps = (1.0 / lv_tick_duration).toFixed(1); // round to 1 decimal behind the dot

            lv_world_settings = lv_state['World'];

            // check what the ID of this world is. Is it still the same world we were expecting, or a different world?
            lv_new_world_ID = lv_state['World']['world_ID'];

            // we request more often than the lv_tick_duration, as to not miss any ticks
            lv_wait_for_next_tick = lv_tick_duration * 1000 * 0.6;

            // request at least every half second
            if (lv_wait_for_next_tick > 500) {
                lv_wait_for_next_tick = 500;
            }

            // note our new current tick
            lv_current_tick = lv_new_tick;

            // make sure to synchronize the play/pause button of the frontend with the current MATRX version
            var matrx_paused = data.matrx_paused;
            if (matrx_paused != lv_matrx_paused) {
                lv_matrx_paused = matrx_paused;
                sync_play_button(lv_matrx_paused);
            }
        },
    });

    return lv_update_request;
}


/*
 * Send the object "data" to MATRX as JSON data. The agent ID is automatically appended.
 */
function send_userinput_to_MATRX(data) {
    // send an update for every key pressed
    var lv_resp = $.ajax({
        method: "POST",
        url: lv_send_userinput_url + lv_agent_id,
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        data: JSON.stringify(data),
        success: function() {
            //console.log("Data sent to MATRX");
        },
    });
    return lv_resp;
}
