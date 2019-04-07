var canvas = null;
var ctx = null;
// width and height of 1 cell = square
var px_per_cell = 40;
// number of cells in width and height of map
var mapW = 10, mapH = 10;
var currentSecond = 0, frameCount = 0, framesLastSecond = 0;
var firstDraw = true;

// Colour of the default BG tile
var bgTileColour = "#C2C2C2";


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
 * Keep track of how often the visualization is updated as frames per second
 */
function calc_fps() {
	var sec = Math.floor(Date.now()/1000);
	if(sec!=currentSecond)
	{
		currentSecond = sec;
		framesLastSecond = frameCount;
		frameCount = 1;
	}
	else { frameCount++; }
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
 * Draw the grid on screen
 */
function drawSim(grid_size, state) {

    // return in the case that the canvas has disappeared
	if(ctx==null) { return; }

    calc_fps();

    // for the first time drawing the visualization, calculate the optimal
    // screen size based on the grid size
    if (firstDraw) {
        console.log("First draw, resetting canvas and tile sizes");
        fixCanvasSize();
        firstDraw = false;
    }

    // save the number of cells in x and y direction of the map
    updateGridSize(grid_size);

    // draw a default bg tile
    drawBg();

    // Draw the grid
    // traverse along Y axis
	for(var y = 0; y < grid_size[1]; ++y)
	{
        // traverse along X axis
		for(var x = 0; x < grid_size[0]; ++x)
		{

            // draw any objects on top
            key = x + "_" + y;
            if (key in state){
                // console.log("Objects for key ", key, ":", state[key]);

                // loop through objects for this possition and draw them
                for (var objKey in state[key]) {
                    obj = state[key][objKey]
                    // console.log('obj:', obj);

                    // get the object colour and size
                    clr = obj['colour'];
                    sz = obj['size'];

                    // draw the object with the correct shape, size and colour
                    if (obj['shape'] == 0) {
                        drawRectangle(x*px_per_cell, y*px_per_cell, px_per_cell, px_per_cell, clr, sz)
                    }
                    else if (obj['shape'] == 1) {
                        drawTriangle(x*px_per_cell, y*px_per_cell, px_per_cell, px_per_cell, clr, sz);
                    }
                }
            }
		}
	}

    // Draw the FPS to the canvas as last so it's drawn on top
	ctx.fillStyle = "#ff0000";
	ctx.fillText("FPS: " + framesLastSecond, 10, 20);
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
