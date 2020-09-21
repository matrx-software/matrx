/*

Parses the MATRX state and generates and updates the grid

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
    vis_settings = null;

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
    latest_tick_processed = null,
    redraw_required = false; // for instance when the window has been resized

// tracked HTML objects
var saved_prev_objs = {}, // obj containing the IDs of objects and their visualization settings of the previous tick
    saved_objs = {}, // obj containing the IDs of objects and their visualization settings of the current tick
    bg_tile_ids = [], // obj_IDS of background tiles
    matrx_tile_ids = []; // obj_IDS of MATRX objects

// track
var object_selected = false; //

/**
 * Get the grid wrapper object
 */
function initialize_grid() {
    grid = document.getElementById("grid");

    navbar = document.getElementById("matrx-toolbar");
}



/**
 * Generate the grid and all its objects
 * @param state: the MATRX state
 * @param world_settings: the MATRX World object, containing all settings of the current MATRX World
 * @param new_messages: object with for every chatroom (ID), the new messages
 * @param accessible_chatrooms: object with for every chatroom (ID), another object with the "name" and "type".
 * @param new_tick: whether this is the first draw after a new tick/update
 */
function draw(state, world_settings, new_messages, accessible_chatrooms, new_tick) {
    // whether to (re)populate the dropdown menu with links to all agents
    populate_god_agent_menu = false;
    pop_new_chat_dropdown = false;

    // parse the new word settings, and change the grid, background, and tiles based on any changes
    // in the settings
    parse_world_settings(world_settings);

    // if we already processed this tick (MATRX is paused), stop and return
    if (latest_tick_processed == current_tick && !redraw_required) {
        return;
    }

    // process any messages received
    process_messages(new_messages, accessible_chatrooms);

    // move the objects from last tick to another list
    saved_prev_objs = saved_objs;
    saved_objs = {};

    // Loop through the IDs of the objects we received in the MATRX state
    var obj_ids = Object.keys(state);
    var saved_prev_obj_keys = Object.keys(saved_prev_objs);
    obj_ids.forEach(function(objID) {

        // skip the World object
        if (objID === "World") {
            return;
        }

        // fetch object from the MATRX state
        obj = state[objID];

        // get the location of the object in pixel values
        var x = obj['location'][0];
        var y = obj['location'][1];

        // fetch bg img if defined
        var obj_img = null;
        if (Object.keys(obj).includes('img_name')) {
            obj_img = fix_img_url(obj['img_name']);
        }

        var show_busy_condition =  (obj.hasOwnProperty("is_blocked_by_action") &&
                                    obj['visualization'].hasOwnProperty('show_busy') &&
                                    obj['visualization']['show_busy']);

        // save visualization settings for this object
        var obj_vis_settings = {
            "img": obj_img,
            "shape": obj['visualization']['shape'],
            "size": obj['visualization']['size'], // percentage how much of tile is filled
            "colour": hexToRgba(obj['visualization']['colour'], obj['visualization']['opacity']),
            "opacity": obj['visualization']['opacity'],
            "dimension": tile_size, // width / height of the tile
            "busy": (show_busy_condition ? obj['is_blocked_by_action'] : false), // show busy if available and requested
            "selected": (object_selected == objID ? true : false)
        };

        // Check if any subtiles have been defined and include them in the ob_vis_settings if so
        if (Object.keys(obj).includes('subtiles') && Object.keys(obj).includes('subtile_loc')) {
            obj_vis_settings['subtiles'] = obj["subtiles"];
            obj_vis_settings['subtile_loc'] = obj["subtile_loc"];
        }

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
            if (obj.hasOwnProperty('isAgent')) {

                console.log("adding selection listener:", objID);
                populate_god_agent_menu = true;
                pop_new_chat_dropdown = true;

                // add a click listener for the selection
                add_selection_listener(obj_element);
            }

            // we already generated this object in a previous tick
        } else {
            // fetch the object from html
            obj_element = document.getElementById(objID);

            // check if the coordinate changed compared to the previous tick, and if so, add css rules
            // for animating the x,y coordinates change
            if (obj_element.style.left != (x * tile_size) + "px" || obj_element.style.top != (y * tile_size) + "px") {
                obj_element.style.setProperty("-webkit-transition", "all " + animation_duration_s + "s");
                obj_element.style.transition = "all " + animation_duration_s + "s";

                // move the object to the new coordinates
                move_object(obj_element, x, y);
            }

            // if nothing changed in the visualisation setting of this obj, we don't need
            // to (re)style the object
            if (compare_objects(saved_prev_objs[objID], obj_vis_settings)) {
                style_object = false;
            }

        }

        // set the visualization depth of this object
        obj_element.style.zIndex = obj['visualization']['depth'];

        // if we need to style this object, e.g. because it's new or visualiation settings changed,
        // regenerate the specfic object shape with its settings
        if (style_object || redraw_required) {

            // repopulate the agent list, when the visualization settings changed of an agent
            if (obj.hasOwnProperty('isAgent')) {
                populate_god_agent_menu = true;
            }

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

    // all objects have been redrawn, so this can be set to false again
    redraw_required = false;

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

        // next time redraw all objects
        redraw_required = true;
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
 * Parse the World object, containing all general information on the current MATRX world.
 * Here functions can also hook into changes in the world (e.g. different grid size)
 */
function parse_world_settings(world_settings) {
    tps = (1.0 / world_settings['tick_duration']).toFixed(1);
    current_tick = world_settings['nr_ticks'];

    if (current_tick > latest_tick_processed + 1) {
        console.log("Dropped frame, current tick:", current_tick, " last tick processed: ", latest_tick_processed);
    }

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
 * Parse the visualization settings passed in the World settings of MATRX. Also changes the bg if needed
 */
function parse_vis_settings(vis_settings) {
    bg_colour = vis_settings['vis_bg_clr'];

    bg_image = null;
    if (Object.keys(vis_settings).includes('vis_bg_img') && vis_settings['vis_bg_img'] != null) {
        bg_image = fix_img_url(vis_settings['vis_bg_img']);
    }

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
 * Updates the grid size as passed in the new MATRX World settings. Regenerates new bg tiles if needed.
 */
function update_grid_size(new_grid_size) {
    if (grid_size == null || new_grid_size[0] != grid_size[0] || new_grid_size[1] != grid_size[1]) {
        grid_size = new_grid_size;
        fix_grid_size();
    }
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

    // use subtiles if they are defined and their location is valid
    if("subtiles" in obj_vis_settings
            && "subtile_loc" in obj_vis_settings
            && obj_vis_settings['subtile_loc'][0] >= 0
            && obj_vis_settings['subtile_loc'][0] < obj_vis_settings['subtiles'][0]
            && obj_vis_settings['subtile_loc'][1] >= 0
            && obj_vis_settings['subtile_loc'][1] < obj_vis_settings['subtiles'][1]) {

        // get width and height of subtile
        tileW = tile_size * (1.0 / obj_vis_settings["subtiles"][0]);
        tileH = tile_size * (1.0 / obj_vis_settings["subtiles"][1]);
        var subtile_tile_sizes = [tileW, tileH];

        // calc the offset of the subtile within the parent tile
        var x_offset = tileW * (obj_vis_settings["subtile_loc"][0]);
        var y_offset = tileH * (obj_vis_settings["subtile_loc"][1]);
        var subtile_offsets = [x_offset, y_offset];

        // offset of the topleft parent tile to the subtile + offset of the object within that subtile
        shape.style.left = subtile_offsets[0] + ((1 - size) * 0.5 * subtile_tile_sizes[0]) + "px";
        shape.style.top = subtile_offsets[1] + ((1 - size) * 0.5 * subtile_tile_sizes[1]) + "px";

        // width and height of rectangle
        shape.style.width = size * subtile_tile_sizes[0] + "px";
        shape.style.height = size * subtile_tile_sizes[1] + "px";

    // subtitle are defined but the subtile_loc is not valid, give a warning in the terminal
    } else if ("subtiles" in obj_vis_settings && "subtile_loc" in obj_vis_settings) {
        console.log("Object with subtiles", obj_vis_settings['subtiles'], ' has subtile_loc',
                obj_vis_settings['subtile_loc'] , ' that is out of range. Drawing without subtile.');

    // no subtiles defined, place the rectangle in the usual manner
    } else {
        // coords of top left corner, such that it is centered in our tile
        shape.style.left = ((1 - size) * 0.5 * tile_size) + "px";
        shape.style.top = ((1 - size) * 0.5 * tile_size) + "px";

        // width and height of rectangle
        shape.style.width = size * tile_size + "px";
        shape.style.height = size * tile_size + "px";
    }

    // styling
    shape.style.background = obj_vis_settings['colour'];

    // remove any old shapes
    while (obj_element.firstChild) {
        obj_element.removeChild(obj_element.firstChild);
    }

    // add a click listener for the context menu
    add_context_menu(shape);

    // add the new shape
    obj_element.append(shape);

    // check if we need to show a loading icon
    if (obj_vis_settings['busy']) {
        var busy_icon = document.createElement('img');
        busy_icon.className = "matrx_object_busy";
        // set the image source
        busy_icon.setAttribute("src", '/static/images/busy_black_small.gif');
        // small loading icon
        busy_icon.style.width = 0.35 * tile_size + "px";
        busy_icon.style.height = 0.35 * tile_size + "px";
        // position in the top left corner
        busy_icon.style.right = "0px";
        busy_icon.style.top = "0px";
        obj_element.append(busy_icon);
    }

    // add selection image if needed
    if (obj_vis_settings['selected']) {
        var selection_img = document.createElement('img');
        selection_img.className = "matrx_object_selected";
        // set the image source
        selection_img.setAttribute("src", '/static/images/selected.png');
        obj_element.append(selection_img);
    }

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

    // for a triangle, we set the content width/height to 0
    shape.style.width = 0;
    shape.style.height = 0;

    // use subtiles if they are defined and their location is valid
    if("subtiles" in obj_vis_settings
            && "subtile_loc" in obj_vis_settings
            && obj_vis_settings['subtile_loc'][0] >= 0
            && obj_vis_settings['subtile_loc'][0] < obj_vis_settings['subtiles'][0]
            && obj_vis_settings['subtile_loc'][1] >= 0
            && obj_vis_settings['subtile_loc'][1] < obj_vis_settings['subtiles'][1]) {

        // get width and height of subtile
        tileW = tile_size * (1.0 / obj_vis_settings["subtiles"][0]);
        tileH = tile_size * (1.0 / obj_vis_settings["subtiles"][1]);
        var subtile_tile_sizes = [tileW, tileH];

        // calc the offset of the subtile within the parent tile
        var x_offset = tileW * (obj_vis_settings["subtile_loc"][0]);
        var y_offset = tileH * (obj_vis_settings["subtile_loc"][1]);
        var subtile_offsets = [x_offset, y_offset];

        // offset of the topleft parent tile to the subtile + offset of the object within that subtile
        shape.style.left = subtile_offsets[0] + ((1 - size) * 0.5 * subtile_tile_sizes[0]) + "px";
        shape.style.top = subtile_offsets[1] + ((1 - size) * 0.5 * subtile_tile_sizes[1]) + "px";

        // We use borders to create the triangle, it is basically the bottom border with
        // the left and right side cut off diagonally by transparent borders on the side
        shape.style.borderBottom = (size * subtile_tile_sizes[0]) + "px solid " + obj_vis_settings['colour'];
        shape.style.borderLeft = (size * subtile_tile_sizes[1] / 2) + "px solid transparent";
        shape.style.borderRight = (size * subtile_tile_sizes[1] / 2) + "px solid transparent";


    // subtitle are defined but the subtile_loc is not valid, give a warning in the terminal
    } else if ("subtiles" in obj_vis_settings && "subtile_loc" in obj_vis_settings) {
        console.log("Object with subtiles", obj_vis_settings['subtiles'], ' has subtile_loc',
                obj_vis_settings['subtile_loc'] , ' that is out of range. Drawing without subtile.');

    // no subtiles defined, place the triangle in the usual manner
     } else {

        // coords of top left corner, such that it is centered in our tile
        shape.style.left = ((1 - size) * 0.5 * tile_size) + "px";
        shape.style.top = ((1 - size) * 0.5 * tile_size) + "px";

        // instead we use borders to create the triangle, it is basically the bottom border with
        // the left and right side cut off diagonally by transparent borders on the side
        shape.style.borderBottom = (size * tile_size) + "px solid " + obj_vis_settings['colour'];
        shape.style.borderLeft = (size * tile_size / 2) + "px solid transparent";
        shape.style.borderRight = (size * tile_size / 2) + "px solid transparent";
    }

    // remove any old shapes
    while (obj_element.firstChild) {
        obj_element.removeChild(obj_element.firstChild);
    }

    // add a click listener for the context menu
    add_context_menu(shape);

    // add the new shape
    obj_element.append(shape);

   // check if we need to show a loading icon
    if (obj_vis_settings['busy']) {
        var busy_icon = document.createElement('img');
        busy_icon.className = "matrx_object_busy";
        // set the image source
        busy_icon.setAttribute("src", '/static/images/busy_black_small.gif');
        // small loading icon
        busy_icon.style.width = 0.35 * tile_size + "px";
        busy_icon.style.height = 0.35 * tile_size + "px";
        // position in the top left corner
        busy_icon.style.right = "0px";
        busy_icon.style.top = "0px";
        obj_element.append(busy_icon);
    }

    // add selected img if needed
    if (obj_vis_settings['selected']) {
        var selection_img = document.createElement('img');
        selection_img.className = "matrx_object_selected";
        // set the image source
        selection_img.setAttribute("src", '/static/images/selected.png');
        obj_element.append(selection_img);
    }

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

    return shape;
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
            tile.style = "left:" + pos_x + "px; top:" + pos_y + "px; width: " + tile_size + "px; height: " + tile_size + "px; z-index: 0;";

            // add context menu
            add_context_menu(tile);

            // add to grid
            grid.append(tile);

            // add id to our list of bg_tile_ids
            bg_tile_ids.push(tile.id);
        }
    }
}


/*********************************************************************
 * Click listeners
 ********************************************************************/

// add an event listener for left mouse clicks, that selects an agent
function add_selection_listener(object) {
    $(object).click( function() {

        console.log("clicked on selection listener");
        var obj = $(this);
        var obj_id = obj.attr('id');

        // clicking twice on the same object deselects it
        if (object_selected == obj_id) {
            deselect(obj_id)

        // deselect any other selected objects, and select the clicked object
        } else {
            if (object_selected != false) {
                deselect(object_selected);
            }

            select(obj_id)
        }
    })

}

// select an object
function select(obj_id) {
    object_selected = obj_id;

    // add selection image
    var selection_img = document.createElement('img');
    selection_img.className = "matrx_object_selected";
    // set the image source
    selection_img.setAttribute("src", '/static/images/selected.png');
    $('#' + obj_id).append(selection_img);
}

// deselect an object
function deselect(obj_id) {
    object_selected = false;
    document.getElementById(obj_id).style.backgroundImage = "none";

    // remove selection image
    $('#' + obj_id).find('.matrx_object_selected').remove()
}

// add an event listener for right mouse clicks, opening the context menu
function add_context_menu(object) {
    $(object).contextMenu({
        menuSelector: "#contextMenu",
        menuSelected: function(invokedOn, selectedMenu) {

            // console.log("Execute API call with message:", selectedMenu[0].mssg)

            var matrx_url = 'http://' + window.location.hostname,
                port = "3001",
                matrx_send_message_pickled = "send_message_pickled";

            post_data = {'sender': lv_agent_id, 'message': selectedMenu[0].mssg}
            // console.log("Sending post data:", post_data);

            var context_menu_request = $.ajax({
                method: "POST",
                data: JSON.stringify(post_data),
                url: matrx_url + ":" + port + "/" + matrx_send_message_pickled,
                contentType: "application/json; charset=utf-8",
                dataType: 'json'
            });

            // console.log("Response:", context_menu_request);

            // if the request gave an error, print to console and try to reinitialize
            context_menu_request.fail(function(data) {
                console.log("Sending context menu input failed:", data.responseJSON)
            });

            // if the request was succesfull, add the options to the menu and show the menu
            context_menu_request.done(function(data) {
                // console.log("Sending context menu input succeeded:", data)
            });

        }
    });
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
 * Compares two objects on equality. Assumes identical order
 */
function compare_objects(o1, o2) {
    if (o1 === undefined || o2 === undefined) {
        return false;
    }

    // stringify to JSON so we can also check nested objects
    if (JSON.stringify(o1) != JSON.stringify(o2)) {
        return false;
    }

    return true;
};

/*
 * Move an object to a new x, y coordinate using css
 */
function move_object(obj_element, x, y) {
    obj_element.style.left = (x * tile_size) + "px";
    obj_element.style.top = (y * tile_size) + "px";
    obj_element.cell_x = x;
    obj_element.cell_y = y;
}

/*
 * Reset the width and height of a tile, e.g. because the grid size changed
 */
function set_tile_dimensions(obj_element) {
    obj_element.style.width = tile_size + "px";
    obj_element.style.height = tile_size + "px";
}
