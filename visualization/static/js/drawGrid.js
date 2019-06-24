/**
 * This is a file which draws the grid with all objects, used for all views:
 * Agent, human-agent and god view.
 */

var canvas = null;
var ctx = null;
var disconnected = false;
// width and height of 1 cell = square
var px_per_cell = 40;
// number of cells in width and height of map
var mapW = 10, mapH = 10;
var currentSecondTicks = 0, tpsCount = 0, ticksLastSecond = 0;
var currentSecondFrames = 0, fpsCount = 0, framesListSecond = 0;
var lastTickSecond = 0;
var firstDraw = true;

// Colour of the default BG tile
var bgTileColour = "#C2C2C2";
var highestTickSoFar = 0;

var prevAnimatedObjects = {};
var animatedObjects = {};
var targetFPS = 60;
// how long should the animation of the movement be, in percentage with respect to
// the maximum number of time available between ticks 1 = max duration between ticks, 0.001 min (no animation)
var animationDurationPerc = 1;


window.onload = function()
{
    canvas = document.getElementById('grid');
	ctx = canvas.getContext("2d");

	ctx.font = "bold 10pt sans-serif";
};

/**
 * Changes the size of the canvas on a window resize such that it is always fullscreen
 */
window.addEventListener("resize", fixCanvasSize );
function fixCanvasSize() {

    // get canvas element from html
    canvas = document.getElementById('grid');

    // resize to current window size
    canvas.width = document.body.clientWidth; //document.width is obsolete
    canvas.height = document.body.clientHeight; //document.height is obsolete

    // change the tiles such that the complete grid fits on the screen
    fixTileSize(canvas.width, canvas.height);

    console.log("Fixed canvas size");
}

/**
 * change the tile size such that it optimally fits on the screen
 */
function fixTileSize(canvasW, canvasH) {

    // calc the pixel per cell ratio in the x and y direcetion
    var px_per_cell_x = Math.round(canvasW / mapW);
    var px_per_cell_y = Math.round(canvasH / mapH);

    // Use the smallest one as the width AND height of the cells to keep tiles square
    px_per_cell = Math.min(px_per_cell_x, px_per_cell_y);
}

/**
 * Keep track of how many ticks per second are received
 */
function calc_fps() {
	var sec = Math.floor(Date.now()/1000);
	if(sec != currentSecondFrames)
	{
		currentSecondFrames = sec;
		framesLastSecond = fpsCount;
		fpsCount = 1;
	}
	else { fpsCount++; }
}

/**
 * Calculate how many frames per second are visualized
 */
function calc_tps() {
    var sec = Math.floor(Date.now()/1000);
	if(sec != currentSecondTicks)
	{
		currentSecondTicks = sec;
		ticksLastSecond = tpsCount;
		tpsCount = 1;
	}
	else { tpsCount++; }
}

/**
 * Stop the GUI if we haven't received a new update for a long while
 */
function checkDisconnected() {
    if (ticksLastSecond == 0 || lastTickSecond == 0) {
        return;
    }

    // if we haven't received a new tick for a while (3x the normal duration), quit the animation loop
    if((lastTickSecond + ((1.0 / ticksLastSecond) * 1000 * 3)) < Date.now()) {
        console.log("Haven't received a new tick in a long while, stopping animated movement updates");
        disconnected = true;
    }
}

/**
 * check if the grid size has changed and recalculate the tile sizes if so
 */
function updateGridSize(grid_size) {
    if (grid_size[0] != mapW || grid_size[1] != mapH) {

        // save the new grid size
        mapW = grid_size[0];
        mapH = grid_size[1];

        // recalculate the sizes of the tiles
        fixTileSize(canvas.width, canvas.height);
    }
}

/**
 * called when a new tick is received by the agent
 */
function doTick(grid_size, state, curr_tick, vis_bg_clr) {
    // for the first time drawing the visualization, calculate the optimal
    // screen size based on the grid size
    if (firstDraw) {
        // console.log("First draw, resetting canvas and tile sizes");
        fixCanvasSize();
        firstDraw = false;
        bgTileColour = vis_bg_clr;
    }

    // console.log("\n#####################################\nNew tick #", curr_tick);

    // calc the ticks per second
    highestTickSoFar = curr_tick;
    lastTickSecond = Date.now();
    calc_tps();
    // the tracked objects from last iteration are moved to a seperate list
    prevAnimatedObjects = animatedObjects;
    animatedObjects = {};

    // console.log("Received state:", state);

    // if we have less than X ticks per second (by default 60), animate the movement
    if (ticksLastSecond < targetFPS && ticksLastSecond > 0) {
        drawSim(grid_size, state, curr_tick, true);
    }
    else {
        drawSim(grid_size, state, curr_tick, false);
    }
}

/**
 * Draw the grid on screen
 */
function drawSim(grid_size, state, curr_tick, animateMovement) {

    // return in the case that the canvas has disappeared
	if(ctx==null) { return; }

    // console.log("Tick:", curr_tick, "highest tick:", highestTickSoFar);

    // return in case there is a new tick, and we are still updating the old tick
    if (curr_tick != highestTickSoFar) {
        // console.log("Updating old tick, return");
        return;
    }
    // console.log("Drawing grid");

    calc_fps();
    updateGridSize(grid_size); // save the number of cells in x and y direction of the map
    drawBg(); // draw a default bg tile

    // identify the objects we received
    var obj_keys = Object.keys(state);

    // calculate a number of necessary variables for timing the movement animation
    if( true ) {
        // how many milliseconds should 1 frame take
        var msPerFrame = (1.0 / targetFPS) * 1000;

        // how many frames should the animation of movement take
        var animationDurationFrames = (targetFPS / ticksLastSecond) * animationDurationPerc;

        // how many milliseconds the animation of movement should take
        var animationDurationMs = animationDurationFrames * msPerFrame;
    }

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

            // if (key.includes("agent")) {
            //     console.log("Agent object:", obj);
            // }

            // keep track of objects which need to be animated
            // if (animateMovement && "animateMovementGUI" in obj) {}
            if (true) {

                // fetch the previous location of the object from last iteration
                if ( !(objID in animatedObjects) && objID in prevAnimatedObjects) {
                    // console.log("Fetching", objID, " from prevAnimatedObjects");
                    animatedObjects[objID] = {"loc_from": prevAnimatedObjects[objID]["loc_to"], "loc_to": obj['location'], "position": cellsToPxs(prevAnimatedObjects[objID]["loc_to"]), "timeStarted": Date.now()};
                }

                // check if we need to animate this movement, which is the case if:
                // it it is our first encounter with this object, or it moves to a new position
                if ( !(objID in animatedObjects && animatedObjects[objID]['loc_from'] == obj['location']) ) {
                    // console.log("This is a moving agent", obj);
                    // console.log("From ", obj["prev_location"][0], obj["prev_location"][1], "(",cellsToPxs(obj["prev_location"])[0], cellsToPxs(obj["prev_location"])[1], ") to", obj["location"][0], obj["location"][1], "(",cellsToPxs(obj["location"])[0], cellsToPxs(obj["location"])[1], ")");
                    var pos = processMovement(objID, obj['location'], animatedObjects, animationDurationMs);
                    // round the location to round pixel values
                    x =  Math.round(pos[0]);
                    y =  Math.round(pos[1]);
                    // console.log("Agent new coordinates:", x, y);
                }
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
            }
            else if (obj['visualization']['shape'] == 1) {
                drawTriangle(x, y, px_per_cell, px_per_cell, clr, sz);
            }
            else if (obj['visualization']['shape'] == 2) {
                drawCircle(x, y, px_per_cell, px_per_cell, clr, sz);
            }
        })
    });

    // Draw the FPS to the canvas as last so it's drawn on top
	ctx.fillStyle = "#ff0000";
	ctx.fillText("FPS: " + framesLastSecond, 10, 20);
	ctx.fillText("TPS: " + ticksLastSecond, 65, 20);

    if (animateMovement) {
        // console.log("Calling draw recursively at:", Date.now(), " with delay in ms: ", msPerFrame);

        // call the draw function again after a short sleep to get to desired number of fps in milliseconds
        setTimeout(function() { drawSim(grid_size, state, curr_tick, animateMovement); }, msPerFrame);
    }
}


/**
 * Converts a list of [x,y] cell coordinates to [x,y] pixel values
 */
function cellsToPxs(coords) {
    return [coords[0] * px_per_cell, coords[1] * px_per_cell]
}

/**
 * Animate the movement from one cell to the target cell for an object, by covering
 * the distance in smaller steps
 */
function processMovement(key, targetLocation, animatedObjects, timePerMove){
    // add the object if this is our first iteration animating its movement
    if ( !(key in prevAnimatedObjects) ) {
        animatedObjects[key] = {"loc_from": targetLocation, "loc_to": targetLocation, "position": cellsToPxs(targetLocation), "timeStarted": Date.now()};
        // console.log("New agent, adding to array, new array", animatedObjects);
        return animatedObjects[key]["position"];
    }

    var obj = animatedObjects[key];
    // console.log("Fetched agent from array:", obj);

    // check if we have completed animating the movement
    if((Date.now() - obj["timeStarted"] >= timePerMove)) {
        animatedObjects[key]["position"] = cellsToPxs(animatedObjects[key]["loc_to"]);

    // otherwise, we move the object a little to the target location
    } else {
        // calc and set the new coordinates for the object
        animatedObjects[key]["position"][0] = calcNewAnimatedCoord(animatedObjects[key], 0, timePerMove);
        animatedObjects[key]["position"][1] = calcNewAnimatedCoord(animatedObjects[key], 1, timePerMove);
    }
    return animatedObjects[key]["position"]
}


/**
 * Calculate a new coordinate of the agent as it moves in small steps
 * to the goal cell.
 * @oaram obj = object for which to calculate the animated movement
 * @param coord = which coordinate we are calculating (x or y).
 * @param timePerMove = milliseconds available for the animated motion from loc_from to loc_to
 */
function calcNewAnimatedCoord(obj, coord, timePerMove) {
    if(obj["loc_to"][coord] != obj["loc_from"][coord]) {
        // calc how many blocks our target is
        var numberOfCellsToMove = Math.abs(obj["loc_to"][coord] - obj["loc_from"][coord]);
        // how many px per ms we should traverse to get to our destination
        var pxPerMs = (numberOfCellsToMove * px_per_cell) / timePerMove;
        // how long have we been moving towards our target
        var msUnderway = Date.now() - obj["timeStarted"];
        // calc our new position
        var diff = msUnderway * pxPerMs;
        // make sure movement is in the correct direction
        diff = (obj["loc_to"][coord] < obj["loc_from"][coord] ? - diff : diff);
        // move in the correct direction from the old position
        obj["position"][coord] = (obj["loc_from"][coord] * px_per_cell) + diff

        // console.log("New animated coord:", numberOfCellsToMove, pxPerMs, msUnderway, diff);
    }
    return obj["position"][coord]
}



/**
 * Draw a background with the default colour
 */
function drawBg() {
    // full size rect
    ctx.fillStyle = bgTileColour;
    ctx.fillRect( 0, 0, mapW * px_per_cell, mapH * px_per_cell);
}



/**
 * Draw a rectangle on screen
 *
 * @param {int} x: x location of tile (top left)
 * @param {int} y: y location of tile (top left)
 * @param {int} tileW: width of normal tile
 * @param {int} tileH: height of normal tile
 * @param {str} clr: colour to be used to fill the figure
 * @param {float} size: size ratio (0-1) of this tile compared to a full tile
 */
function drawRectangle(x, y, tileW, tileH, clr, size) {
    // coords of top left corner
    top_left_x = x + ((1 - size) * 0.5 * tileW);
    top_left_y = y + ((1 - size) * 0.5 * tileH);

    // width and height of rectangle
    w = size * tileW;
    h = size * tileH;

    // draw the rectangle
    ctx.fillStyle = clr;
    ctx.fillRect( top_left_x, top_left_y, w, h);
}

/**
 * Draw a circle on screen
 *
 * @param {int} x: x location of tile (top left)
 * @param {int} y: y location of tile (top left)
 * @param {int} tileW: width of normal tile
 * @param {int} tileH: height of normal tile
 * @param {str} clr: colour to be used to fill the figure
 * @param {float} size: size ratio (0-1) of this tile compared to a full tile
 */
function drawCircle(x, y, tileW, tileH, clr, size) {
    // coords of top left corner
    top_x = x + 0.5 * tileW;
    top_y = y + 0.5 * tileH;

    // width and height of rectangle
    w = size * tileW;
    h = size * tileH;

    // draw the rectangle
    // ctx.fillRect( top_left_x, top_left_y, w, h);
    ctx.beginPath();
    ctx.arc(top_x, top_y, w * 0.5, 0, 2 * Math.PI);
    ctx.closePath();

    // fill the shape with colour
    ctx.fillStyle = clr;
    ctx.fill();
}


/**
 * Draw a triangle on screen
 *
 * @param {int} x: x location of tile (top left)
 * @param {int} y: y location of tile (top left)
 * @param {int} tileW: width of normal tile
 * @param {int} tileH: height of normal tile
 * @param {str} clr: colour to be used to fill the figure
 * @param {float} size: size ratio (0-1) of this tile compared to a full tile
 */
function drawTriangle(x, y, tileW, tileH, clr, size) {
    // calc the coordinates of the top corner of the triangle
    topX = x + 0.5 * tileW;
    topY = y + ((1 - size) * 0.5 * tileH);

    // calc the coordinates of the bottom left corner of the triangle
    bt_leftX = x + ((1 - size) * 0.5 * tileW);
    bt_leftY = y + tileH - ((1 - size) * 0.5 * tileH);

    // calc the coordinates of the bottom right corner of the triangle
    bt_rightX = x + tileW - ((1 - size) * 0.5 * tileW);
    bt_rightY = y + tileH - ((1 - size) * 0.5 * tileH);

    // draw triangle point by point
    ctx.beginPath();
    ctx.moveTo(topX, topY); // center top
    ctx.lineTo(bt_leftX, bt_leftY); // bottom left
    ctx.lineTo(bt_rightX, bt_rightY); // bottom right
    ctx.closePath();

    // fill the shape with colour
    ctx.fillStyle = clr;
    ctx.fill();
}

/**
 * Convert a hexadecimal colour code to an RGBA colour code
 */
function hexToRgba(hex, opacity) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? "rgba(" + parseInt(result[1], 16) + "," + parseInt(result[2], 16)
                        + "," + parseInt(result[3], 16) + "," + opacity + ")" : null;
}
