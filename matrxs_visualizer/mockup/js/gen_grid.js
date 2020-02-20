/*

Parses the MATRXS state and generates and updates the grid

*/

// GUI settings
// How long should the animation of the movement be, in percentage with respect to
// the maximum number of time available between ticks 1 = max duration between ticks, 0.001 min (no animation)
// Note: it is not recommended to set this value to higher than ~0.9, as the exact duration between ticks can
// slightly vary between ticks, resulting in jittery movement
var animation_duration_perc = 0.8;

// Variables that will be parsed from the World settings
var tps = null,
    current_tick = null,
    world_ID = null,
    grid_size = null;
    vis_settings = null,
    messages = {}; // our database with messages, indexed by chat room name

// Visualization settings
var prev_bg_image = null,
    bg_image = null,
    bg_colour = null,
    prev_bg_colour = null;

// vars for the working of the GUI
var firstDraw = true,
    tile_size = null, // in Pixels. tiles are always square, so width and height are the same
    navbar = null,
    animation_duration_s = null, // is calculated based on animation_duration_perc and tps.
    populate_god_agent_menu = null, // keep track of any new agents
    pop_new_chat_dropdown = null,
    latest_tick_processed = null;

// tracked HTML objects
var saved_prev_objs = {}, // obj containing the IDs of objects and their visualization settings of the previous tick
    saved_objs = {}, // obj containing the IDs of objects and their visualization settings of the current tick
    bg_tile_ids = [], // obj_IDS of background tiles
    matrxs_tile_ids = []; // obj_IDS of MATRXS objects

/**
 * Get the grid wrapper object
 */
function initialize_grid() {
    grid = document.getElementById("grid");

    navbar = document.getElementById("matrxs-toolbar");
}



/**
 * Generate the grid and all its objects
 * @param state: the MATRXS state
 * @param world_settings: the MATRXS World object, containing all settings of the current MATRXS World
 * @param new_messages: object containing lists with "private", "team", and "global" messages for the current agent
 * @param accessible_chatrooms: object containing the "private", "teams" and "global" chatrooms accessible by the
 *                              current agent.
 * @param new_tick: whether this is the first draw after a new tick/update
 */
function draw(state, world_settings, new_messages, accessible_chatrooms, new_tick) {
    // whether to (re)populate the dropdown menu with links to all agents
    populate_god_agent_menu = false;
    pop_new_chat_dropdown = false

    // parse the new word settings, and change the grid, background, and tiles based on any changes
    // in the settings
    parse_world_settings(world_settings);

    // if we already processed this tick (MATRX is paused), stop and return
    if (latest_tick_processed == current_tick) {
        return;
    }

    // process any messages received
    process_messages(new_messages);

    // move the objects from last tick to another list
    saved_prev_objs = saved_objs;
    saved_objs = {};

    // Loop through the IDs of the objects we received in the MATRXS state
    var obj_ids = Object.keys(state);
    var saved_prev_obj_keys = Object.keys(saved_prev_objs);
    obj_ids.forEach(function(objID) {

        // skip the World object
        if (objID === "World") {
            return;
        }

        // fetch object from the MATRXS state
        obj = state[objID];

        // get the location of the object in pixel values
        var x = obj['location'][0] * tile_size;
        var y = obj['location'][1] * tile_size;

        // fetch bg img if defined
        var obj_img = null;
        if (Object.keys(obj).includes('img_name')) {
            obj_img = obj['img_name'];
        }

        // save visualization settings for this object
        var obj_vis_settings = {
            "img": obj_img,
            "shape": obj['visualization']['shape'],
            "size": obj['visualization']['size'], // percentage how much of tile is filled
            "colour": hexToRgba(obj['visualization']['colour'], obj['visualization']['opacity']),
            "opacity": obj['visualization']['opacity'],
            "dimension": tile_size // width / height of the tile
        };

        var obj_element = null; // the html element of this object
        var animate_movement = false; // whether any x,y position changes should be animated
        var object_is_new = false; // whether this is a new object, not present in the html yet
        var style_object = true; // whether this object should be regenerated, e.g. because vis settings changed

        // check if this is a new object
        if (!saved_prev_obj_keys.includes(objID)) {
            // create a html element for this object and set classes / ID
            obj_element = document.createElement("div");
            obj_element.className = "object";
            obj_element.id = objID;

            // set the coordinates of the object
            move_object(obj_element, x, y);

            // this is a new object
            new_object = true;

            // add to grid
            grid.append(obj_element);

            // add this agent to the dropdown list
            if (obj_element.hasOwnProperty('isAgent')) {
                populate_god_agent_menu = true;
                pop_new_chat_dropdown = true;
            }

            // we already generated this object in a previous tick
        } else {
            // fetch the object from html
            obj_element = document.getElementById(objID);

            // check if the coordinate changed compared to the previous tick, and if so, add css rules
            // for animating the x,y coordinates change
            if (obj_element.style.left != (x * tile_size) || obj_element.style.top != (y * tile_size)) {
                obj_element.style.setProperty("-webkit-transition", "all " + animation_duration_s + "s");
                obj_element.style.transition = "all " + animation_duration_s + "s";

                // move the object to the new coordinates
                move_object(obj_element, x, y);
            }

            // if nothing changed in the visualisation setting of this obj, we don't need
            // to (re)style the object
            if (compare_objects(saved_prev_objs[objID], obj_vis_settings)) {
                style_object = false;

                // repopulate the agent list, when the visualization settings changed of an agent
                if (obj_element.hasOwnProperty('isAgent')) {
                    populate_god_agent_menu = true;
                    pop_new_chat_dropdown = true;
                }
            }
        }

        // set the visualization depth of this object
        obj_element.style.zIndex = obj['vis_depth'];

        // if we need to style this object, e.g. because it's new or visualiation settings changed,
        // regenerate the specfic object shape with its settings
        if (style_object) {
            set_tile_dimensions(obj_element);

            // draw the object with the correct shape, size and colour
            if (obj_vis_settings['img'] != null) {
                gen_image(obj_vis_settings, obj_element);
            } else if (obj_vis_settings['shape'] == 0) {
                gen_rectangle(obj_vis_settings, obj_element);
            } else if (obj_vis_settings['shape'] == 1) {
                gen_triangle(obj_vis_settings, obj_element);
            } else if (obj_vis_settings['shape'] == 2) {
                gen_circle(obj_vis_settings, obj_element);
            }
        }

        // add the object ID and the visualization settings to the saved_objs list of the current tick
        saved_objs[objID] = obj_vis_settings;

        // remove this item from our list of tracked objs from the previous tick
        saved_prev_obj_keys = saved_prev_obj_keys.filter(function(e) {
            return e !== objID
        })
    });

    // any objects present in the previous tick but not present in the current
    // tick should be removed
    saved_prev_obj_keys.forEach(function(objID) {
        remove_element(objID);
    });

    // (re)populate the dropdown menu with links to all agents
    if (lv_agent_id == "god" && populate_god_agent_menu) {
        populate_agent_menu(state);
    }

    // update the list with accessible chatrooms
    if (pop_new_chat_dropdown) {
        populate_new_chat_dropdown(accessible_chatrooms);
    }

    // mark this tick as processed (in the case the user paused MATRX)
    latest_tick_processed = current_tick;

    // Draw the FPS to the canvas as last so it's drawn on top
    // TODO: draw tps?
    //    ctx.fillStyle = "#ff0000";
    //    ctx.fillText("TPS: " + tps, 65, 20);
}


/*************************************************************************************
 * Responsiveness of the visualization to screen size or grid size adjustments
 *************************************************************************************/

window.addEventListener("resize", fix_grid_size);

function fix_grid_size() {

    // calc and fix the new tile size, given the maximum possible dimensions of the grid
    if (fix_tile_size()) {
        console.log("Objects regenerated");
        // redraw the background if the tile size changed
        draw_bg_tiles();

        // resize the grid to exactly encompass all tiles
        grid.style.width = tile_size * grid_size[0] + "px";
        grid.style.height = tile_size * grid_size[1] + "px";
    }

    console.log("Fixed tile and grid size");
}

/**
 * Calc how much height and width is available for the grid
 */
function get_max_grid_dimensions() {
    // height is page height minus navbar
    var height = document.documentElement.clientHeight - navbar.scrollHeight;

    // width is full page width
    var width = document.documentElement.clientWidth;
    return [height, width];
}

/**
 * Given the size of the grid, calculate how large the tiles should be to fill the maximum amount of room while
 * remaining the correct ratio (square tiles). Returns whether the tile size changed or not.
 */
function fix_tile_size() {
    // calc the available size for the grid
    var available_height = null,
        available_width = null;
    [available_height, available_width] = get_max_grid_dimensions();

    // calc the pixel per cell ratio in the x and y direction
    var px_per_cell_x = Math.floor(available_width / grid_size[0]);
    var px_per_cell_y = Math.floor(available_height / grid_size[1]);

    // Use the smallest one as the width AND height of the cells to keep tiles square
    var new_tile_size = Math.min(px_per_cell_x, px_per_cell_y);

    // check if anything changed
    if (new_tile_size != tile_size) {
        // save the new tile size
        tile_size = new_tile_size;

        // return that the tile size has changed
        return true
    }

    // we did not have to change the tile size
    return false
}



/*********************************************************************
 * Parsing of the world state
 ********************************************************************/

/**
 * Parse the World object, containing all general information on the current MATRXS world.
 * Here functions can also hook into changes in the world (e.g. different grid size)
 */
function parse_world_settings(world_settings) {
    tps = (1.0 / world_settings['tick_duration']).toFixed(1);
    current_tick = world_settings['nr_ticks'];

    // reset some things if we are visualizing a new world
    if (world_ID != world_settings['world_ID']) {
        // if it is not the first load of a world, but a genuine transition to a new world, reset
        // the chat
        if (world_ID != null) {
            reset_chat();
        }
        populate_god_agent_menu = true;
        pop_new_chat_dropdown = true;
    }
    world_ID = world_settings['world_ID'];

    // calculate how many milliseconds the movement animation should take
    animation_duration_s = (1.0 / tps) * animation_duration_perc;

    // parse new visualization settings
    vis_settings = world_settings['vis_settings'];
    parse_vis_settings(vis_settings);

    // update grid
    update_grid_size(world_settings['grid_shape']);
}

/**
 * Parse the visualization settings passed in the World settings of MATRXS. Also changes the bg if needed
 */
function parse_vis_settings(vis_settings) {
    bg_colour = vis_settings['vis_bg_clr'];
    bg_image = vis_settings['vis_bg_img'];

    // update background colour / image if needed
    draw_bg();
}


/**
 * Checks the background specifications (colour, image), as specified in the World object, and changes the
 * grid accordingly if needed
 */
function draw_bg() {

    // change bg colour if needed
    if (prev_bg_colour != bg_colour) {
        prev_bg_colour = bg_colour;
        grid.style.backgroundColor = bg_colour;
    }

    // change bg image if needed
    if (prev_bg_image != bg_image) {
        prev_bg_image = bg_image;
        grid.style.backgroundImage = "url('" + bg_image + "')";
    }
}


/**
 * Updates the grid size as passed in the new MATRXS World settings. Regenerates new bg tiles if needed.
 */
function update_grid_size(new_grid_size) {
    if (grid_size == null || new_grid_size[0] != grid_size[0] || new_grid_size[1] != grid_size[1]) {
        grid_size = new_grid_size;
        fix_grid_size();
    }
}


/*********************************************************************
 * Processing of new messages
 ********************************************************************/
/*
 * Process the object containing messages of various types, received from MATRX, and process them
 * into individual messages.
 */
function process_messages(new_messages) {
    var mssg_types = ["global", "team", "private"];

    // process all messages of all types
    mssg_types.forEach(function(mssg_type) {

        // loop through the ticks in the message objects
        Object.keys(new_messages[mssg_type]).forEach(function(tick) {
            // skip this tick if we have no messages
            if (new_messages[mssg_type][tick] == null) {
                return;

                // Team messages go one layer deeper, divided into teams, before getting to the messgs
            } else if (mssg_type == "team") {
                Object.keys(new_messages[mssg_type][tick]).forEach(function(team) {
                    // add every message of every tick
                    (new_messages[mssg_type][tick][team]).forEach(function(mssg) {
                        process_message(mssg_type, JSON.parse(mssg), team);
                    });
                });

                // private / global messages are all directly listed under tick
            } else {
                // add every message of every tick
                new_messages[mssg_type][tick].forEach(function(mssg) {
                    process_message(mssg_type, JSON.parse(mssg));
                });
            }
        });
    });
}

/*
 * Process an individual message
 */
function process_message(type, message, team = null) {

    var chat_room = null;

    // for team messages, the team is sent along, which has the same name of our target chat room
    if (type == "team" && team != null) {
        chat_room = team;

        // global messages go in the global chat
    } else if (type == "global") {
        chat_room = "global";

        // for private messages, the chat room's name is that of the ID of the other agent
    } else if (type == "private") {
        chat_room = (message.from_id != lv_agent_id ? message.from_id : message.to_id);
    }

    // open new chatrooms if needed, and display all old messages
    if (!(type == "global") && !chatrooms_added[type].includes(chat_room)) {
        add_chatroom(chat_room, type, set_active = false);
        // repopulate the new chat room dropdown
        populate_new_chat_dropdown(all_chatrooms);
    }

    // add chat_room if needed
    if (!Object.keys(messages).includes(chat_room)) {
        messages[chat_room] = [];
    }

    // add message to list
    messages[chat_room].push(message);

    // add message to GUI
    if (current_chatwindow['name'] == chat_room && current_chatwindow['type'] == type) {
        add_message(chat_room, message);
    } else {
        // show the notification for the chat room
        document.getElementById("chatroom_" + chat_room + "_notification").style.display = "inline-block";
    }

    // repopulate the new chat room dropdown
    pop_new_chat_dropdown = true;
}

/*
 * On pageload, all relevant messages are request from MATRX, and sent to this function for
 * processing and visualizing in the GUI.
 */
function process_mssgs_pageload(initial_mssgs, initial_chatrooms) {
    console.log("Processing mssgs initial pageload:");
    console.log(initial_mssgs);
    console.log(initial_chatrooms);

    // process the chatrooms
    populate_new_chat_dropdown(initial_chatrooms);

    // add every message, adding chatrooms if needed
    process_messages(initial_mssgs);
}


/*********************************************************************
 * Generate objects
 ********************************************************************/

/**
 * Generate the css for a rectangle
 *
 * @param {Object} obj_vis_settings: contains the visualization settings of the object
 * @param {HTML Element} obj_element: contains the HTML element of the object
 * @param {String} element_type: (optional) can be used to specify what type of HTML element should be added
 */
function gen_rectangle(obj_vis_settings, obj_element, element_type = "div") {
    var size = obj_vis_settings['size'];

    // if the object has a smaller size than 1, we create a centered subobject
    var shape = document.createElement(element_type);
    shape.className = "shape";

    // coords of top left corner, such that it is centerd in our tile
    shape.style.left = ((1 - size) * 0.5 * tile_size);
    shape.style.top = ((1 - size) * 0.5 * tile_size);

    // width and height of rectangle
    shape.style.width = size * tile_size + "px";
    shape.style.height = size * tile_size + "px";

    // styling
    shape.style.background = obj_vis_settings['colour'];

    // remove any old shapes
    while (obj_element.firstChild) {
        obj_element.removeChild(obj_element.firstChild);
    }

    // add a click listener for the context menu
    if (lv_agent_type != "agent") {
        add_context_menu(shape);
    }

    // add the new shape
    obj_element.append(shape);
    return shape;
}


/**
 * Generate the css for a triangle
 *
 * @param {Object} obj_vis_settings: contains the visualization settings of the object
 * @param {HTML Element} obj_element: contains the HTML element of the object
 */
function gen_triangle(obj_vis_settings, obj_element) {
    var size = obj_vis_settings['size'];

    // create a centered subobject
    var shape = document.createElement('div');
    shape.className = "shape";

    // coords of top left corner, such that it is centerd in our tile
    shape.style.left = ((1 - size) * 0.5 * tile_size);
    shape.style.top = ((1 - size) * 0.5 * tile_size);

    // for a triangle, we set the content width/height to 0
    shape.style.width = 0;
    shape.style.height = 0;

    // instead we use borders to create the triangle, it is basically the bottom border with
    // the left and right side cut off diagonally by transparent borders on the side
    shape.style.borderBottom = (size * tile_size) + "px solid " + obj_vis_settings['colour'];
    shape.style.borderLeft = (size * tile_size / 2) + "px solid transparent";
    shape.style.borderRight = (size * tile_size / 2) + "px solid transparent";

    // remove any old shapes
    while (obj_element.firstChild) {
        obj_element.removeChild(obj_element.firstChild);
    }

    // add a click listener for the context menu
    if (lv_agent_type != "agent") {
        add_context_menu(shape);
    }

    // add the new shape
    obj_element.append(shape);
    return shape;
}


/**
 * Generate a circle with css. This is a rectangle with rounded corners.
 *
 * @param {Object} obj_vis_settings: contains the visualization settings of the object
 * @param {HTML Element} obj_element: contains the HTML element of the object
 */
function gen_circle(obj_vis_settings, obj_element) {
    // generate a rectangle
    var shape = gen_rectangle(obj_vis_settings, obj_element);

    // round the corners
    shape.style.borderRadius = "50%";

    return shape;
}

/**
 * Add an image html object. This is a rectangle with an image src added
 *
 * @param {Object} obj_vis_settings: contains the visualization settings of the object
 * @param {HTML Element} obj_element: contains the HTML element of the object
 */
function gen_image(obj_vis_settings, obj_element) {
    // add a rectangular "img" HTML element
    var shape = gen_rectangle(obj_vis_settings, obj_element, element_type = "img");

    // set the image source
    shape.setAttribute("src", obj_vis_settings["img"]);

    // set the background as transparent
    shape.style.background = "transparent";
    shape.style.opacity = obj_vis_settings["opacity"];

    shape.dataset.toggle = "dropdown";

    return shape;
}

// add an event listener for mouse clicks, opening the context menu
function add_context_menu(object) {
    $(object).contextMenu({
        menuSelector: "#contextMenu",
        menuSelected: function(invokedOn, selectedMenu) {
            var msg = "You selected the menu item '" + selectedMenu.text() +
                "' on the value '" + invokedOn.text() + "'";
            alert(msg);
        }
    });
}


/**
 * Regenerate all bg tiles in the correct size
 */
function draw_bg_tiles() {

    // remove previous bg tiles
    bg_tile_ids.forEach(function(bg_tile_id) {
        remove_element(bg_tile_id);
    });
    bg_tile_ids = [];

    // add new background tiles
    for (var x = 0; x < grid_size[0]; x++) {
        for (var y = 0; y < grid_size[1]; y++) {

            // create bg tile and set classes / ID
            var tile = document.createElement("div");
            tile.className = "tile";
            tile.id = "tile_" + x + "_" + y;

            // add click listeners
            tile.setAttribute("onmousedown", "startDrawErase(id)");
            tile.setAttribute("onmouseup", "stopDrag()");

            // set position and z-index
            var pos_x = x * tile_size;
            var pos_y = y * tile_size;
            tile.style = "left:" + pos_x + "px; top:" + pos_y + "px; width: " + tile_size + "px; height: " + tile_size + "px; z-index: 0;"

            // add to grid
            grid.append(tile);

            // add id to our list of bg_tile_ids
            bg_tile_ids.push(tile.id);
        }
    }
}


/*********************************************************************
 * Helper methods
 ********************************************************************/

/**
 * Removes an element by ID
 */
function remove_element(id) {
    var elem = document.getElementById(id);
    return elem.parentNode.removeChild(elem);
}


/**
 * Convert a hexadecimal colour code to an RGBA colour code
 */
function hexToRgba(hex, opacity) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? "rgba(" + parseInt(result[1], 16) + "," + parseInt(result[2], 16) +
        "," + parseInt(result[3], 16) + "," + opacity + ")" : null;
}

/**
 * Compares two objects on equality
 */
function compare_objects(o1, o2) {
    if (o1 === undefined || o2 === undefined) {
        return false;
    }
    for (var p in o1) {
        if (o1.hasOwnProperty(p)) {
            if (o1[p] !== o2[p]) {
                return false;
            }
        }
    }
    for (var p in o2) {
        if (o2.hasOwnProperty(p)) {
            if (o1[p] !== o2[p]) {
                return false;
            }
        }
    }
    return true;
};

/*
 * Move an object to a new x, y coordinate using css
 */
function move_object(obj_element, x, y) {
    obj_element.style.left = x + "px";
    obj_element.style.top = y + "px";
}

/*
 * Reset the width and height of a tile, e.g. because the grid size changed
 */
function set_tile_dimensions(obj_element) {
    obj_element.style.width = tile_size + "px";
    obj_element.style.height = tile_size + "px";
}
