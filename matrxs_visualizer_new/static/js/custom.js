function run() {
  var view_mode = document.getElementById("view_mode").value;
  var view_page = view_mode + ".html";
  window.location.href = view_page;
}

function sendMessage() {
  var message = document.getElementById("message_input").value;
  var div = document.createElement("div");
  div.className = "message_you";
  div.innerHTML = message;
  document.getElementById("messages").appendChild(div);
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

function add_draw_erase_classes(class_name) {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
      tiles[i].className = "tile " + class_name;  // Change class of all tiles so that they are highlighted when hovered
    }
    var objects = document.getElementsByClassName("object");
    for (var i = 0; i < objects.length; i++) {
      objects[i].className = "object " + class_name;  // Change class of all tiles so that they are highlighted when hovered
    }
}

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

var draw_activated = false;
function drawToggle() {
    console.log("Toggled");
  if (erase_activated) {
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

var erase_activated = false;
function eraseToggle() {
  if (draw_activated) {
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

function eraseHoverEnter(tile_id) {
  var tile = document.getElementById(tile_id);
  tile.style.backgroundColor = "blue";
}

function eraseHoverLeave(tile_id) {
  var tile = document.getElementById(tile_id);
  tile.style.backgroundColor = "";
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

function startDrawErase(tile_id) {
  if (draw_activated) {
    drawCell(tile_id);
    startDrawDrag();
  }
  if (erase_activated) {
    eraseCell(tile_id);
    startEraseDrag();
  }
}

function drawCell(tile_id) {
  if (draw_activated) {
    var tile = document.getElementById(tile_id);
    tile.style.backgroundColor = "crimson";
  }
}

function startDrawDrag() {
  var tiles = document.getElementsByClassName("tile");
  for (var i = 0; i < tiles.length; i++) {
    tiles[i].setAttribute("onmouseenter", "drawCell(id)");
  }
}

function stopDrag() {
  var tiles = document.getElementsByClassName("tile");
  for (var i = 0; i < tiles.length; i++) {
    tiles[i].setAttribute("onmouseenter", "");
  }
}

function eraseCell(tile_id) {
  if (erase_activated) {
    var tile = document.getElementById(tile_id);
    tile.style.backgroundColor = "";
  }
}

function startEraseDrag() {
  var tiles = document.getElementsByClassName("tile");
  for (var i = 0; i < tiles.length; i++) {
    tiles[i].setAttribute("onmouseenter", "eraseCell(id)");
  }
}

function drawCellOld(tile_id) {
  if (draw_activated) {
    var tile = document.getElementById(tile_id);
    if (getComputedStyle(tile).backgroundColor == "rgb(220, 20, 60)") {
      tile.style.backgroundColor = "";
    } else {
      tile.style.backgroundColor = "crimson";
    }
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

/*************************************
 Newly added for connecting to MATRXS
**************************************/
function clickObject(object_id) {
  document.getElementById("object_modal_label").innerHTML = object_id;
}

