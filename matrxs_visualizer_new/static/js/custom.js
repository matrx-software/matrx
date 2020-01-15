function run() {
  var view_mode = document.getElementById("view_mode").value;
  var view_page = view_mode + ".html";
  window.location.href = view_page;
}

function clickAgent(agent_id) {
  document.getElementById("agent_modal_label").innerHTML = agent_id;
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

var draw = false;
function drawToggle() {
  draw = !draw;
  if (draw) {
    document.getElementById("draw_button").className = "btn btn-secondary";
    var cells = document.getElementsByClassName("cell");
    for (var i = 0; i < cells.length; i++) {
      cells[i].className = "cell draw_mode";  // Change class of all cells so that they are highlighted when hovered
    }
  } else {
    document.getElementById("draw_button").className = "btn btn-dark";
    var cells = document.getElementsByClassName("cell");
    for (var i = 0; i < cells.length; i++) {
      cells[i].className = "cell";
    }
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

function drawCell(cell_id) {
  if (draw) {
    var cell = document.getElementById(cell_id);
    if (getComputedStyle(cell).backgroundColor == "rgb(220, 20, 60)") {
      cell.style.backgroundColor = "";
    } else {
      cell.style.backgroundColor = "crimson";
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
