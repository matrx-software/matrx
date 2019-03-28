// make connection with python server via socket
var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

// Event handler for new connections.
socket.on('connect', function() {
    socket.emit('my_event', {data: 'I\'m connected!'});
    console.log("Connected");
});

// receive a test update from the python server
socket.on('test', function(data){
    console.log("got a message:", data);
});


// receive an update from the python server
socket.on('update', function(data){
    console.log("got a message:", data);

    // draw the screen again
    requestAnimationFrame(drawSim);
});

// send message to Python server every 1 second
// setInterval(function() {
//     socket.emit("test", "yo from agent GUI");
//     console.log("Sending test");
// }, 1000);


// Catch userinput with arrow keys
// Arrows keys: up=1, right=2, down=3, left=4
document.onkeydown = checkArrowKey;
function checkArrowKey(e) {
    e = e || window.event;

    if (e.keyCode == '38') {
        // up arrow
        socket.emit("userinput", {"movement": 1});
    }
    else if (e.keyCode == '39') {
       // right arrow
       socket.emit("userinput", {"movement": 2});
    }
    else if (e.keyCode == '40') {
        // down arrow
        socket.emit("userinput", {"movement": 3});
    }
    else if (e.keyCode == '37') {
       // left arrow
       socket.emit("userinput", {"movement": 4});
    }
}


// gamemap stuff
var ctx = null;
var gameMap = [
	0, 1, 2, 3, 4, 0, 0, 0, 0, 0,
	0, 1, 1, 1, 0, 1, 1, 1, 1, 0,
	0, 1, 0, 0, 0, 1, 0, 0, 0, 0,
	0, 1, 3, 1, 4, 1, 1, 1, 1, 0,
	0, 1, 0, 1, 0, 0, 0, 1, 1, 0,
	0, 1, 0, 1, 3, 1, 0, 0, 1, 0,
	0, 1, 1, 1, 1, 1, 1, 1, 1, 0,
	0, 1, 0, 0, 0, 0, 0, 1, 0, 0,
	0, 1, 1, 1, 0, 1, 1, 1, 1, 0,
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0
];
var tileW = 40, tileH = 40;
var mapW = 10, mapH = 10;
var currentSecond = 0, frameCount = 0, framesLastSecond = 0;


// Shapes of tiles
var tileShapes = {
    0 : "square",
    1 : "triangle"
}

// tileTypes
// colour = hex code colour, shape = titleShapes shape, size = size of tile [0-1]
var tileTypes = {
	0 : { colour:"#685b48", shape:0, size:1},
	1 : { colour:"#5aa457", shape:0, size:1},
	2 : { colour:"#000000", shape:0, size:0.5},
	3 : { colour:"#286625", shape:1, size:1},
	4 : { colour:"#678fd9", shape:1, size:0.5}
};

window.onload = function()
{
    // Get the grid canvas
	ctx = document.getElementById('grid').getContext("2d");
    // request the canvas to draw the grid with our drawSim function
	requestAnimationFrame(drawSim);
	ctx.font = "bold 10pt sans-serif";
};

function drawSim() {
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
	for(var y = 0; y < mapH; ++y)
	{
		for(var x = 0; x < mapW; ++x)
		{

            // set colour of tile
            ctx.fillStyle = tileTypes[gameMap[toIndex(x,y)]].colour;
            sz = tileTypes[gameMap[toIndex(x,y)]].size

            // draw the shape
            switch(tileTypes[gameMap[toIndex(x,y)]].shape)
			{
                case 1:
					drawTriangle(x*tileW, y*tileH, tileW, tileH, sz);
					break;
				default:
                    drawRectangle(x*tileW, y*tileH, tileW, tileH, sz)
            }
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

    console.log(x, y, tileW, tileH, size)

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
