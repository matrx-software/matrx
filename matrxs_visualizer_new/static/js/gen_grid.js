/*

Parses the MATRXS state and generates and updates the grid

*/


// Variables that will be parsed from the World settings
var tps = null;
    current_tick = null,
    world_ID = null,
    grid_size = null;
    vis_settings = null;

// Visualization settings
var prev_bg_image = null,
    bg_image = null,
    bg_colour = null,
    prev_bg_colour = null;

// tracked HTML objects
var bg_tile_ids = [], // obj_IDS of background tiles
    matrxs_tile_ids = []; // obj_IDS of MATRXS objects


var firstDraw = true,
    tile_size = null, // in Pixels. tiles are always square, so width and height are the same
    navbar = null;

var prev_obj_ids = null,
    obj_ids = null,
    saved_prev_objs = {}, // obj containing the IDs of objects and their visualization settings of the previous tick
    saved_objs = {}; // obj containing the IDs of objects and their visualization settings of the current tick


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
 * @param new_tick: whether this is the first draw after a new tick/update
 */
function draw(state, world_settings, new_tick) {

    // parse the new word settings, and change the grid, background, and tiles based on any changes in the settings
    if (new_tick) {
        parse_world_settings(world_settings);
    }

    // identify the objects we received
    var obj_keys = Object.keys(state);

    // calculate how many frames the animation of movement should take
    var animationDurationFrames = (framesLastSecond / tps) * animationDurationPerc;

    // calculate how many milliseconds the movement animation should take
    var animationDurationMs = animationDurationFrames * msPerFrame;

    // move the objects from last tick to another list
    saved_prev_objs = saved_objs;
    saved_objs = {};

    // Loop through the visualization depths
    var vis_depths = Object.keys(state);
    var saved_prev_obj_keys = Object.keys(saved_prev_objs);
    vis_depths.forEach(function(vis_depth) {

        // Loop through the objects at this depth and visualize them
        var objects = Object.keys(state[vis_depth]);
        objects.forEach(function(objID) {

            // skip the World object
            if (objID === "World") {
                return;
            }

            // fetch object from the MATRXS state
            obj = state[vis_depth][objID];

            // fetch location of object in pixel values
            var x = obj['location'][0] * tile_size;
            var y = obj['location'][1] * tile_size;

            // set position in css
            var obj_style = "left:" + pos_x + "px; top:" + pos_y + "px; width: " + tile_size + "px; height: " + tile_size + "px;";

            // fetch bg img if defined
            var obj_img = null;
            if (Object.keys(obj).includes('img_name')) {
                obj_img =  obj['img_name']
            }

            // save visualization settings for this object
            var obj_vis_settings = {"img": obj_img,
                                "shape": obj['visualization']['shape'],
                                "size": obj['visualization']['size'],
                                "colour": hexToRgba(obj['visualization']['colour'], obj['visualization']['opacity']),


            var obj_element = null; // the html element of this object
            var animate_movement = false; // whether any x,y position changes should be animated
            var object_is_new = false; // whether this is a new object, not present in the html yet
            var generate_object = true; // whether this object should be regenerated, e.g. because vis settings changed

            // check if this is a new object
            if (! saved_prev_obj_keys.includes(objID)) {
                // create a html element for this object and set classes / ID
                var obj_element = document.createElement("div");
                obj_element.className = "tile";
                obj_element.id = objID;

                // this is a new object
                new_object = true;

                // add to grid
                grid.append(obj_element);

            // we already generated this object in a previous tick
            } else {
                // fetch the object from html
                obj_element = document.getElementById(objID);

                // check if the coordinate changed compared to the previous tick, and if so, add css rules
                // for animating the x,y coordinates change
                if (obj_element.style.left != x || obj_element.style.top != y) {
                    obj_style += "-webkit-transition: left " + (animationDurationMs/1000) + "s;";
                    obj_style += "-webkit-transition: top " + (animationDurationMs/1000) + "s;";
                    obj_style += "transition: left " + (animationDurationMs/1000) + "s;";
                    obj_style += "transition: top " + (animationDurationMs/1000) + "s";
                }

                // if nothing changed in the visualisation settubg of this obj, we don't need to regenerate the object
                if (saved_prev_objs[objID] == obj_vis_settings) {
                    generate_object = false;
                }
            }

            // assign the css to the object
            obj_element.style = obj_style;

            // if we need to generate this object, e.g. because it's new or visualiation settings changed,
            // regenerate the specfic object type with its settings
            if (generate_object) {
                // draw the object with the correct shape, size and colour
                if (obj_vis_settings['shape'] == 0) {
                    drawRectangle(obj_vis_settings, obj_element);
                } else if (obj_vis_settings['shape'] == 1) {
                    drawTriangle(x, y, obj_vis_settings, obj_element);
                } else if (obj_vis_settings['shape'] == 2) {
                    drawCircle(obj_vis_settings, obj_element);
                } else if (obj_vis_settings['img'] != null) {
                    drawImage(obj_vis_settings, obj_element);
                }
            }

            // add the object ID and the visualization settings to the saved_objs list
            saved_objs[objID] = obj_vis_settings;

            // TODO: remove old objects from HTML which are not present anymore 
            saved_prev_obj_keys
        });
    });

    // Draw the FPS to the canvas as last so it's drawn on top
    ctx.fillStyle = "#ff0000";
    ctx.fillText("TPS: " + tps, 65, 20);
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
    world_ID = world_settings['world_ID'];

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
        grid.style.backgroundColor =  bg_colour;
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
 * Generate objects
 ********************************************************************/

/**
 * Generate the css for a rectangle
 *
 * @param {Object} obj_vis_settings: contains the visualization settings of the object
 * @param {HTML Element} obj_element: contains the HTML element of the object
 * @param {String} element_type: (optional) can be used to specify what type of HTML element should be added
 */
function genRectangle(obj_vis_settings, obj_element, element_type="div") {
    // if it is size 1, simply set the color of the tile object and we are done
    if (size == 1 && element_type != "img") {
        obj_element.style.backgroundColor = clr; // set colour
        obj_element.style.borderRadius = "0"; // remove any round corners
        return obj_element;
    }

    // if the object has a smaller size than 1, we create a centered subobject
    var shape_obj = document.createElement(element_type);
    shape_obj.className = "shape";

    // coords of top left corner, such that it is centerd in our tile
    shape.style.left = x + ((1 - size) * 0.5 * tile_size);
    shape.style.top = y + ((1 - size) * 0.5 * tile_size);

    // width and height of rectangle
    shape.style.width = size * tile_size;
    shape.style.height = size * tile_size;

    // remove any old shapes
    while (obj_element.firstChild) {
        obj_element.removeChild(obj_element.firstChild);
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
function drawTriangle(obj_vis_settings, obj_element) {

    // create a centered subobject
    var shape_obj = document.createElement(element_type);
    shape_obj.className = "shape";

    // coords of top left corner, such that it is centerd in our tile
    shape.style.left = x + ((1 - size) * 0.5 * tile_size);
    shape.style.top = y + ((1 - size) * 0.5 * tile_size);

    // for a triangle, we set the content width/height to 0
    shape.style.width = 0;
    shape.style.height = 0;

    // instead we use borders to create the triangle, it is basically the bottom border with
    // the left and right side cut off diagonally by transparent borders on the side
    shape.style.borderBottom = (size * tile_size) + "px solid " + obj_vis_settings['colour'];
    shape.style.borderLeft = (size * tile_size / 2) + "px solid transparent";
    shape.style.borderRight = (size * tile_size / 2) + "px solid transparent";

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
function genCircle(obj_vis_settings, obj_element) {
    // generate a rectangle
    var shape = genRectangle(obj_vis_settings, obj_element);

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
function drawImage(obj_vis_settings, obj_element) {
    // add a rectangular "img" HTML element
    var shape = genRectangle(obj_vis_settings, obj_element, element_type="img");

    // set the image source
    shape.setAttribute("src", obj_vis_settings["img"]);

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

            // set position
            var pos_x = x * tile_size;
            var pos_y = y * tile_size;
            tile.style = "left:" + pos_x + "px; top:" + pos_y + "px; width: " + tile_size + "px; height: " + tile_size + "px;";

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