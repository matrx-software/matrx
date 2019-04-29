var canvas = null;
var ctx = null;
// width and height of 1 cell = square
var px_per_cell = 40;
// number of cells in width and height of map
var mapW = 10, mapH = 10;
var currentSecondTicks = 0, tpsCount = 0, ticksLastSecond = 0;
var currentSecondFrames = 0, fpsCount = 0, framesListSecond = 0;
var firstDraw = true;

// Colour of the default BG tile
var bgTileColour = "#C2C2C2";
var highestTickSoFar = 0;

var animatedObjects = {};
var targetFPS = 60;
// how quick is the animation of the movement, 1 = max duration between ticks,
// 0.0001 is quickest possible animation
var timePerMoveMultiplier = 1;
var sleepPeriod = 0.0;


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

    // console.log("Reset canvas size to:", canvas.width, canvas.height);

    // change the tiles such that the complete grid fits on the screen
    fixTileSize(canvas.width, canvas.height);

    console.log("Fixed canvas size");
}

/**
 * change the tile size such that it optimally fits on the screen
 */
function fixTileSize(canvasW, canvasH) {

    // calc the pixel per cell ratio in the x and y direcetion
    var px_per_cell_x = canvasW / mapW;
    var px_per_cell_y = canvasH / mapH;

    // Use the smallest one as the width AND height of the cells to keep tiles square
    px_per_cell = Math.min(px_per_cell_x, px_per_cell_y);

    // console.log("Fixed tile size. x, y, min", px_per_cell_x, px_per_cell_y, px_per_cell);
}

/**
 * Keep track of how many ticks per second are received
 */
function calc_fps() {
	var sec = Math.floor(Date.now()/1000);
	if(sec!=currentSecondFrames)
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
	if(sec!=currentSecondTicks)
	{
		currentSecondTicks = sec;
		ticksLastSecond = tpsCount;
		tpsCount = 1;
	}
	else { tpsCount++; }
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
function doTick(grid_size, state, curr_tick) {
    // for the first time drawing the visualization, calculate the optimal
    // screen size based on the grid size
    if (firstDraw) {
        console.log("First draw, resetting canvas and tile sizes");
        fixCanvasSize();
        firstDraw = false;
    }

    // calc the ticks per second
    highestTickSoFar = curr_tick;
    calc_tps();
    // reset tracked animated objects
    animatedObjects = {};

    sleepPeriod = (1.0 / targetFPS) * (fpsCount / tpsCount);


    // if we have less than 60 ticks per second
    if (ticksLastSecond < 60) {
        console.log("starting animation loop, ticksLastSecond:", ticksLastSecond);
        // draw the grid recusively with animated movement
        drawSim(grid_size, state, curr_tick, true);
    }
    else {
        drawSim(grid_size, state, curr_tick, false);
    }
}


// sleep time expects milliseconds
function sleep (time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

/**
 * Draw the grid on screen
 */
function drawSim(grid_size, state, curr_tick, animateMovement) {

    // return in the case that the canvas has disappeared
	if(ctx==null) { return; }

    // return in case there is a new tick, and we are still updating the old tick
    if (curr_tick < highestTickSoFar) {
        highestTickSoFar = curr_tick;
        return;
    }

    calc_fps();
    updateGridSize(grid_size); // save the number of cells in x and y direction of the map
    drawBg(); // draw a default bg tile

    // identify the objects we received
    var obj_keys = Object.keys(state);

    // how much time do we have to animate a movement
    var timePerMove = ((1.0 / targetFPS) * (fpsCount / tpsCount)) * timePerMoveMultiplier;
    console.log("Tps", tpsCount, " fps", fpsCount , " time per tick", timePerMove);

    // Draw the grid
    // loop through objects to draw
    obj_keys.forEach(function(key) {
        var obj = state[key];

        // fetch location of object in pixel values
        var x = obj['location'][0] * px_per_cell;
        var y = obj['location'][1] * px_per_cell;

        // check if we need to animate this movement
        // if (obj["animate"]) {
        if (animateMovement && key.includes("agent")) {
            console.log("This is an agent", obj);
            var pos = processMovement(key, obj["prev_location"], animatedObjects, timePerMove);
            // round the location to round pixel values
            x =  Math.round(pos[0]);
            y =  Math.round(pos[1]);
        }

        // get the object colour and size
        clr = obj['colour'];
        sz = obj['size'];

        // draw the object with the correct shape, size and colour
        if (obj['shape'] == 0) {
            drawRectangle(x, y, px_per_cell, px_per_cell, clr, sz)
        }
        else if (obj['shape'] == 1) {
            drawTriangle(x, y, px_per_cell, px_per_cell, clr, sz);
        }
    });


    // Draw the FPS to the canvas as last so it's drawn on top
	ctx.fillStyle = "#ff0000";
	ctx.fillText("FPS: " + framesLastSecond, 10, 20);
	ctx.fillText("TPS: " + ticksLastSecond, 65, 20);

    if (animateMovement) {
        // short sleep to get to desired number of fps in milliseconds
        sleep((1.0 / targetFPS) * 1000.0);
        // call the animation recusively for animating of movement
        drawSim(grid_size, state, curr_tick, animateMovement)
    }
}


/**
 * Process the movement of an object if it needs to be animated
 */
function processMovement(key, prev_location, animatedObjects, timePerMove){
    // add the object if this is our first iteration animating its movement
    if (!(key in animatedObjects)) {
        animatedObjects[key] = {"loc_from": prev_location, "loc_to": location, "position": location, "timeStarted": Date.now()};
        return animatedObjects[key]["position"]
    }

    var obj = animatedObjects[key];

    // check if we have completed animating the movement
    if((Date.now() - obj["timeStarted"] >= timePerMove)) {
        animatedObjects[key]["position"] = animatedObjects[key]["loc_to"];

    // otherwise, we move the object a little to the target location
    } else {
        // calc and set the new coordinates for the object
        animatedObjects[key]["position"][0] = calcNewAnimatedCoord(animatedObjects[key], 0);
        animatedObjects[key]["position"][1] = calcNewAnimatedCoord(animatedObjects[key], 1);
    }
    return animatedObjects[key]["position"]
}


/**
 * Calculate a new coordinate of the agent as it moves in an animated fashion
 * to the goal state.
 * @oaram obj = object for which to calculate the animated movement
 * @param coord = which coordinate we are calculating (x or y).
 */
function calcNewAnimatedCoord(obj, coord) {
    if(obj["loc_to"][coord] != obj["loc_from"][coord]) {
        // calc how many blocks our target is
        var numberOfCellsToMove = Math.abs(obj["loc_to"][coord] - obj["loc_from"][coord]);
        // calc how much we have moved so far towards the goal location
        var diff = ((numberOfCellsToMove * px_per_cell) / timePerMove) * (Date.now() - obj["timeStarted"]);
        // calc how much will move now and what the new coordinate is
        return (obj["loc_to"][coord] < obj["loc_from"][coord] ? 0 - diff : diff);
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
