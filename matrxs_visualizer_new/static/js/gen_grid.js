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
var bg_image = null,
    bg_colour = null;

// tracked HTML objects
var bg_tile_ids = [], // obj_IDS of background tiles
    matrxs_tile_ids = []; // obj_IDS of MATRXS objects


var firstDraw = true,
    tile_size = null, // in Pixels. tiles are always square, so width and height are the same
    style = null;

/**
 * Get the grid wrapper object
 */
function initialize_grid() {
    grid = document.getElementById("grid");

    // create a stylesheet for managing the dimensions of individual tiles
    style = document.createElement('style');
    style.innerHTML = ".tile { width: 10px; height: 10px;}"; // placeholder width and height
    style.appendChild(document.createTextNode(""));
    document.head.appendChild(style);
}

window.addEventListener("resize", fix_grid_size);
function fix_grid_size() {

    // calc and fix the new tile size, given the maximum possible dimensions of the grid
    fix_tile_size(document.body.clientWidth, document.body.clientHeight);

    // resize the grid to exactly encompass all tiles
    grid.style.width = tile_size * grid_size[0];
    grid.style.height = tile_size * grid_size[1];

    console.log("Fixed tile and grid size");
}

/**
 * Given the size of the grid, calculate how large the tiles should be to fill the maximum amount of room while
 * remaining the correct ratio (square tiles).
 */
function fix_tile_size(max_width, max_height) {
    // calc the pixel per cell ratio in the x and y direction
    var px_per_cell_x = Math.round(max_width / grid_size[0]);
    var px_per_cell_y = Math.round(max_height / grid_size[1]);

    // Use the smallest one as the width AND height of the cells to keep tiles square
    var new_tile_size = Math.min(px_per_cell_x, px_per_cell_y);

    // fix the tile sizes of all tiles by changing the class
    if (new_tile_size != tile_size) {
        // save the new tile size
        tile_size = new_tile_size;

        // change the CSS class such that all tiles are the correct width/height in one go
        style.innerHTML = ".tile { width: " + new_tile_size + "px; height: " + new_tile_size + "px;}";
    }
}

/**
 * Draw all objects on the canvas
 * @param state: the MATRXS state
 * @param world_settings: the MATRXS World object, containing all settings of the current MATRXS World
 * @param new_tick: whether this is the first draw after a new tick/update
 */
function draw(state, world_settings, new_tick) {

    // parse the new word settings, and change the grid, background, and tiles based on any changes in the settings
    if (new_tick) {
        parse_world_settings(world_settings);
    }

    // Loop through the visualization depths
    var vis_depths = Object.keys(state);
    vis_depths.forEach(function(vis_depth) {

        // Loop through the objects at this depth and visualize them
        var objects = Object.keys(state[vis_depth]);
        objects.forEach(function(objID) {


        });
    });

}


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
    bg_colour = vis_settings['visualization_bg_clr'];
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
    if (grid.style.backgroundColor != bg_colour) {
        grid.setAttribute("background-color", bg_colour);
    }

    // change bg image if needed
    if (grid.style.backgroundImage != bg_image) {
        grid.setAttribute("background-image", bg_image);
    }
}


/**
 * Updates the grid size as passed in the new MATRXS World settings. Regenerates new bg tiles if needed.
 */
function update_grid_size(new_grid_size) {
    if (grid_size == null || new_grid_size[0] != grid_size[0] || new_grid_size[1] != grid_size[1]) {
        grid_size = new_grid_size;
        draw_bg_tiles();
    }
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

    // Now that all tiles have been removed, we can safely recalc the tile size without
    // anything shifting on screen
    fix_tile_size();

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
            tile.style = "position:absolute; left:" + pos_x + "px; top:" + pos_y + "px;";

            // add to grid
            grid.append(tile);

            // add id to our list of bg_tile_ids
            bg_tile_ids.push(tile.id);
        }
    }
}


/**
 * Removes an element by ID
 */
function remove_element(id) {
    var elem = document.getElementById(id);
    return elem.parentNode.removeChild(elem);
}

