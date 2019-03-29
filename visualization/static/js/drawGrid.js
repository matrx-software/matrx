
// gamemap stuff
var canvas = null;
var ctx = null;
// width and height of 1 cell = square
// var tileW = 40, tileH = 40;
var px_per_cell = 40;
// number of cells in width and height of map
var mapW = 10, mapH = 10;
var currentSecond = 0, frameCount = 0, framesLastSecond = 0;
// init
var firstDraw = true;

// Colour of the default BG tile
var bgTileColour = "#C2C2C2";

window.onload = function()
{
    canvas = document.getElementById('grid');
	ctx = canvas.getContext("2d");

    // // resize the canvas to be fullscreen
    // fixCanvasSize();

	ctx.font = "bold 10pt sans-serif";
};


// Changet the size of the canvas on a resize such that it is always fullscreen
window.addEventListener("resize", fixCanvasSize );
function fixCanvasSize() {

    // get canvas from html
    canvas = document.getElementById('grid');

    // resize to current window size
    canvas.width = document.body.clientWidth; //document.width is obsolete
    canvas.height = document.body.clientHeight; //document.height is obsolete

    console.log("Reset canvas size to:", canvas.width, canvas.height);

    // change the tiles such that the complete grid fits on the screen
    fixTileSize(canvas.width, canvas.height);
}

// change the tile size such that it optimally fits on the screen
function fixTileSize(canvasW, canvasH) {

    // calc the pixel per cell ratio in the x and y direcetion, and use
    // the smallest one as the width ANd height of the cells, to keep them square
    var px_per_cell_x = canvasW / mapW;
    var px_per_cell_y = canvasH / mapH;
    px_per_cell = Math.min(px_per_cell_x, px_per_cell_y);

    console.log("Fixed tile size. x, y, min", px_per_cell_x, px_per_cell_y, px_per_cell);
}

function calc_fps() {
    // Keep track of our Frames per second
	var sec = Math.floor(Date.now()/1000);
	if(sec!=currentSecond)
	{
		currentSecond = sec;
		framesLastSecond = frameCount;
		frameCount = 1;
	}
	else { frameCount++; }
}

// check if the grid size has changed, and recalculate the tile sizes if so
function updateGridSize() {
    if (grid_size[0] != mapW || grid_size[1] != mapH) {

        // save the new grid size
        mapW = grid_size[0];
        mapH = grid_size[1];

        // recalculate the sizes of the tiles
        fixTileSize(canvas.width, canvas.height);
    }
}

function drawSim(grid_size, state) {
    // return in the case that the canvas has disappeared
	if(ctx==null) { return; }

    calc_fps();

    // on the first draw run, calculate the optimal screen size based on the grid size
    if (firstDraw) {
        console.log("First draw, resetting canvas and tile sizes");
        fixCanvasSize();
        firstDraw = false;
    }

    // save the number of cells in x and y direction of the map
    updateGridSize();

    console.log("Drawing sim")

    // draw the grid
    // Traverse along Y axis
	for(var y = 0; y < grid_size[1]; ++y)
	{
        // traverse along X axis
		for(var x = 0; x < grid_size[0]; ++x)
		{
            // draw a default bg tile
            drawBgTile(x, y, px_per_cell, px_per_cell);

            // draw any objects
            key = x + "_" + y;
            if (key in state){
                // console.log("Objects for key ", key, ":", state[key]);

                // loop through objects for this possition and draw them
                for (var objKey in state[key]) {
                    obj = state[key][objKey]
                    // console.log('obj:', obj);

                    // set the correct colour
                    ctx.fillStyle = obj['colour'];

                    sz = obj['size'];

                    if (obj['shape'] == 0) {
                        drawRectangle(x*px_per_cell, y*px_per_cell, px_per_cell, px_per_cell, sz)
                    }
                    else if (obj['shape'] == 1) {
                        drawTriangle(x*px_per_cell, y*px_per_cell, px_per_cell, px_per_cell, sz);
                    }

                }

            }
            // else {
            //     console.log("No objects for key ", key);
            // }

            // // set colour of tile
            // ctx.fillStyle = tileTypes[gameMap[toIndex(x,y)]].colour;
            // sz = tileTypes[gameMap[toIndex(x,y)]].size
            //
            // // draw the shape
            // switch(tileTypes[gameMap[toIndex(x,y)]].shape)
			// {
            //     case 1:
			// 		drawTriangle(x*tileW, y*tileH, tileW, tileH, sz);
			// 		break;
			// 	default:
            //         drawRectangle(x*tileW, y*tileH, tileW, tileH, sz)
            // }
		}
	}

    // Draw the FPS to the canvas as last so it's drawn over other things
	ctx.fillStyle = "#ff0000";
	ctx.fillText("FPS: " + framesLastSecond, 10, 20);

    // request another animationFrame, which will draw the map again
	// requestAnimationFrame(drawSim);
}



// convert x,y coord to map index
function toIndex(x, y) {
	return((y * mapW) + x);
}

// Draw a bg tile with a default colour
function drawBgTile(x, y, tileW, tileH) {
    // full size rect
    ctx.fillStyle = bgTileColour;
    ctx.fillRect( x*tileW, y*tileH, tileW, tileH);
}


// draw rectangle
// x = x location of tile (top left)
// y = y location of tile (top left)
// tileW = width of normal tile
// tileH = height of normal tile
// size = size ratio (0-1) of normal tile
function drawRectangle(x, y, tileW, tileH, size) {
    // full size rect
    // ctx.fillRect( x*tileW, y*tileH, tileW, tileH);

    // coords of top left corner
    top_left_x = x + ((1 - size) * 0.5 * tileW);
    top_left_y = y + ((1 - size) * 0.5 * tileH);
    // width and height of rectangle
    w = size * tileW;
    h = size * tileH;

    ctx.fillRect( top_left_x, top_left_y, w, h);
}

// draw a triangle
// x = x location of tile (top left)
// y = y location of tile (top left)
// tileW = width of normal tile
// tileH = height of normal tile
// size = size ratio (0-1) of normal tile
function drawTriangle(x, y, tileW, tileH, size) {

    // calc the coordinates of the top corner of the triangle
    topX = x + 0.5 * tileW;
    topY = y + ((1 - size) * 0.5 * tileH);
    // calc the coordinates of the bottom left corner of the triangle
    bt_leftX = x + ((1 - size) * 0.5 * tileW);
    bt_leftY = y + tileH - ((1 - size) * 0.5 * tileH);
    // calc the coordinates of the bottom right corner of the triangle
    bt_rightX = x + tileW - ((1 - size) * 0.5 * tileW);
    bt_rightY = y + tileH - ((1 - size) * 0.5 * tileH);

    // draw triangle
    ctx.beginPath();
    ctx.moveTo(topX, topY); // center top
    ctx.lineTo(bt_leftX, bt_leftY); // bottom left
    ctx.lineTo(bt_rightX, bt_rightY); // bottom right
    ctx.closePath();

    // fill with colour
    ctx.fill();
}
