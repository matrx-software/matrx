window.onload = function()
{

    // 120 0 40 40 1
    // agent.js:153 160 0 40 40 0.5 (normal size)
    // agent.js:153 80 120 40 40 1
    // agent.js:153 160 120 40 40 0.5 (upside down)
    // agent.js:153 160 200 40 40 1

    x = 160;
    y = 0;
    tileW = 40;
    tileH = 40;

    size = 0.5;

    topX = x + 0.5 * tileW;
    topY = y + ((1 - size) * 0.5 * tileH);

    bt_leftX = x + ((1 - size) * 0.5 * tileW);
    bt_leftY = y + tileH - ((1 - size) * 0.5 * tileH);

    bt_rightX = x + tileW - ((1 - size) * 0.5 * tileW);
    bt_rightY = y + tileH - ((1 - size) * 0.5 * tileH);

    // Get the grid canvas
	ctx = document.getElementById('grid').getContext("2d");

    ctx.beginPath();
    ctx.moveTo(topX, topY); // center top
    ctx.lineTo(bt_leftX, bt_leftY); // bottom left
    ctx.lineTo(bt_rightX, bt_rightY); // bottom right
    ctx.closePath();

    // ctx.beginPath();
    // ctx.moveTo(x + (tileW * 0.5), y); // center top
    // ctx.lineTo(x, y + tileH); // bottom left
    // ctx.lineTo(x + tileW, y + tileH); // bottom right
    // ctx.closePath();

    ctx.fillStyle = "#FFCC00";
    ctx.fill();


};
