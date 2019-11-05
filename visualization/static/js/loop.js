/**
 * In this file the loop is managed for requesting updates via the MATRXS API, and calling the draw functions for
 * updating the visualization.
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
var agent_id = "";


var state = {}



/*
 * Once the page has loaded, call the initialization function
 */
$(document).ready(function() {
    init();
});

/*
 * Initialize the visualization by requesting the MATRXS scenario info.
 * If successful, the main visualization loop is called
 */
function init() {
    console.log("initializing");

    var path = window.location.pathname;
    // get the type ("" for god, "agent" or "human-agent") from the URL
    var type = path.substring(0, path.lastIndexOf('/'));
    if (type != "") {type = type.substring(1)};
    // Get the agent ID from the url (e.g. "god", "agent_0123", etc.)
    var ID = path.substring(path.lastIndexOf('/') + 1).toLowerCase();

    // check if this view is for the god view, agent, or human-agent, and get the correct urls
    if (type == "" && ID == "god") {
        console.log("This is the god view");
    } else if (type == "agent") {
        agent_id = ID;
        console.log("This view is for an Agent with ID:", agent_id);
    } else if (type == "human-agent") {
        agent_id = ID;
        console.log("This view is for a Human Agent with ID:", agent_id);
    }


    // fetch settings
    var resp = jQuery.getJSON(init_url, function(data) {
        // on success, start the visualization loop
        initialized = true;
        tick_duration = data.tick_duration;
        current_tick = data.tick;
        grid_size = data.grid_size;

        console.log("Fetched MATRXS settings:", data);

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



