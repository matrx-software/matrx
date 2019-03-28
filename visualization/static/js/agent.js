// make connection with python server via socket
var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

// Event handler for new connections.
socket.on('connect', function() {
    socket.emit('my_event', {data: 'I\'m connected!'});
    console.log("Connected");
});

// receive an update from the python server
socket.on('update', function(data){
    console.log("Received an update from the server:", data);

    grid_size = data.params.grid_size;
    state = data.state;

    // draw the screen again
    requestAnimationFrame(function() {
        drawSim(grid_size, state);
    });
});



// gamemap stuff
var ctx = null;
var tileW = 40, tileH = 40;
var mapW = 10, mapH = 10;
var currentSecond = 0, frameCount = 0, framesLastSecond = 0;


// Colour of the default BG tile
var bgTileColour = "#C2C2C2";

window.onload = function()
{
    // Get the grid canvas
	ctx = document.getElementById('grid').getContext("2d");
    // request the canvas to draw the grid with our drawSim function
	// requestAnimationFrame(drawSim);
	ctx.font = "bold 10pt sans-serif";
};

function drawSim(grid_size, state) {
	if(ctx==null) { return; }

    console.log("Drawing sim")

    // Keep track of our Frames per second
	var sec = Math.floor(Date.now()/1000);
	if(sec!=currentSecond)
	{
		currentSecond = sec;
		framesLastSecond = frameCount;
		frameCount = 1;
	}
	else { frameCount++; }


    // draw the grid
    // Traverse along Y axis
	for(var y = 0; y < grid_size[1]; ++y)
	{
        // traverse along X axis
		for(var x = 0; x < grid_size[0]; ++x)
		{
            // draw a default bg tile
            drawBgTile(x, y, tileW, tileH);

            // draw any objects
            key = x + "_" + y;
            if (key in state){
                console.log("Objects for key ", key, ":", state[key]);

                // loop through objects for this possition and draw them
                for (var objKey in state[key]) {
                    obj = state[key][objKey]
                    console.log('obj:', obj);

                    // set the correct colour
                    ctx.fillStyle = obj['colour'];

                    sz = obj['size'];

                    if (obj['shape'] == 0) {
                        drawRectangle(x*tileW, y*tileH, tileW, tileH, sz)
                    }
                    else if (obj['shape'] == 1) {
                        drawTriangle(x*tileW, y*tileH, tileW, tileH, sz);
                    }

                }

            }
            else {
                console.log("No objects for key ", key);
            }

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
