function run() {
    var view_mode = document.getElementById("view_mode").value;
    var view_page = view_mode + ".html";
    window.location.href = view_page;
}

function sendMessage() {
    var message = document.getElementById("message_input").value;
    message = message.trim();
    console.log("Message:", message, message.length);
    if (!message || 0 === message.length) {
        return;
    }
    var div = document.createElement("div");
    div.className = "message_you";
    div.innerHTML = message;
    var messages = document.getElementById("messages");
    messages.insertBefore(div, messages.firstChild);
    document.getElementById("message_input").value = null;
}

function selectContact(agent_id) {
    var prev_contact_active = document.getElementsByClassName("contact_active")[0];
    prev_contact_active.className = "contact";

    var contact = document.getElementsByClassName("contact").namedItem(agent_id);
    contact.className = "contact contact_active";

    // TODO should be linked to a database of messages
    var messages = document.getElementById("messages");
    while (messages.firstChild) {
        messages.removeChild(messages.firstChild);
    }
}

var message_input = document.getElementById("message_input");
message_input.onkeypress = function(event) {
    if (event.keyCode == 13) {
        sendMessage();
    }
}

// Change class of all tiles so that they are highlighted when hovered
function add_draw_erase_classes(class_name) {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].className = "tile " + class_name;
    }
    var objects = document.getElementsByClassName("object");
    for (var i = 0; i < objects.length; i++) {
        objects[i].className = "object " + class_name;
    }
}

// Change class of all tiles so that they are no longer highlighted when hovered
function remove_draw_erase_classes() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].className = "tile";
    }
    var objects = document.getElementsByClassName("object");
    for (var i = 0; i < objects.length; i++) {
        objects[i].className = "object";
    }
}

// Called when draw button is clicked. Enables/disables draw function
var draw_activated = false;

function drawToggle() {
    if (erase_activated) { // If the erase function is active, disable it
        eraseToggle();
    }
    draw_activated = !draw_activated;
    if (draw_activated) {
        document.getElementById("draw_button").className = "btn btn-secondary";
        add_draw_erase_classes("draw_mode");
    } else {
        document.getElementById("draw_button").className = "btn btn-dark";
        remove_draw_erase_classes();
    }
}

// Called when erase button is clicked. Enables/disables erase function
var erase_activated = false;

function eraseToggle() {
    if (draw_activated) { // If the draw function is active, disable it
        drawToggle();
    }
    erase_activated = !erase_activated;
    if (erase_activated) {
        document.getElementById("erase_button").className = "btn btn-secondary";
        add_draw_erase_classes("erase_mode");
    } else {
        document.getElementById("erase_button").className = "btn btn-dark";
        remove_draw_erase_classes();
    }
}

// Called when a tile is clicked. Draws/erases the tile and starts drag function that allows the user to draw/erase multiple tiles while holding the left mouse button
function startDrawErase(tile_id) {
    if (draw_activated) {
        drawTile(tile_id);
        startDrawDrag();
    }
    if (erase_activated) {
        eraseTile(tile_id);
        startEraseDrag();
    }
}

function drawTile(tile_id) {
    if (draw_activated) {
        var tile = document.getElementById(tile_id);
        tile.style.backgroundColor = "crimson";
    }
}

function startDrawDrag() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].setAttribute("onmouseenter", "drawTile(id)");
    }
}

function stopDrag() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].setAttribute("onmouseenter", "");
    }
}

function eraseTile(tile_id) {
    if (erase_activated) {
        var tile = document.getElementById(tile_id);
        tile.style.backgroundColor = "";
    }
}

function startEraseDrag() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].setAttribute("onmouseenter", "eraseTile(id)");
    }
}

var chat = false;

function chatToggle() {
    chat = !chat;
    if (chat) {
        document.getElementById("chat_button").className = "btn btn-secondary";
    } else {
        document.getElementById("chat_button").className = "btn btn-dark";
    }
}

function initGrid() {
    var rows = 8;
    var columns = 8;
    var grid = document.getElementById("grid");
    var row = document.createElement("div").className = "row";

    for (var i = 0; i < columns; i++) {
        grid.appendChild(row);
    }

}

function agentAction(agent_id) {
    alert(agent_id + "_performs action");
}

var out = document.getElementById("messages");
var c = 0;
var add = setInterval(function() {
    // allow 1px inaccuracy by adding 1
    var isScrolledToBottom = out.scrollHeight - out.clientHeight <= out.scrollTop + 1;
    // scroll to bottom if isScrolledToBottom
    if(isScrolledToBottom)
      out.scrollTop = out.scrollHeight - out.clientHeight;
}, 1000);

/*************************************
 Newly added for connecting to MATRXS
**************************************/
function clickObject(object_id) {
    document.getElementById("object_modal_label").innerHTML = object_id;
}
