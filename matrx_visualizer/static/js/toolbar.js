// data on the MATRX API
var matrx_url = 'http://' + window.location.hostname,
    port = "3001",
    matrx_send_message_url = "send_message";


/*********************************************************************
 * Simulation control buttons in toolbar (start/pause etc.)
 ********************************************************************/

// Toolbar elements
var start_button = document.getElementById("start_button"),
    pause_button = document.getElementById("pause_button"),
    stop_button = document.getElementById("stop_button");

/**
 * Synchronizes the play/pause button with the current value of MATRX
 */
function sync_play_button(matrx_paused) {

    console.log("syncing play/pause button, matrx_paused:", matrx_paused);
    // hide the play button and show the pause button
    if (!matrx_paused) {
        start_button.classList.add("hidden");
        pause_button.classList.remove("hidden");

        // vice versa
    } else {
        start_button.classList.remove("hidden");
        pause_button.classList.add("hidden");
    }
}

start_button.addEventListener("click", toggle_start, false);

function toggle_start() {
    console.log("pressed play");
    // hide / unhide the correct button
    start_button.classList.toggle("hidden");
    pause_button.classList.toggle("hidden");

    // send API message to MATRX
    send_api_message("start");
}

pause_button.addEventListener("click", toggle_pause, false);

function toggle_pause() {
    console.log("pressed pause");
    // hide / unhide the correct button
    start_button.classList.toggle("hidden");
    pause_button.classList.toggle("hidden");

    // send API message to MATRX
    send_api_message("pause");
}


stop_button.addEventListener("click", toggle_stop, false);

function toggle_stop() {
    send_api_message("stop");
}


/**
 * Send a message to the MATRX API
 */
function send_api_message(type) {
    var resp = $.ajax({
        method: "GET",
        url: matrx_url + ":" + port + "/" + type,
        contentType: "application/json; charset=utf-8",
        dataType: 'json'
    });
}

function send_matrx_api_post_message(type, post_data) {
    var resp = $.ajax({
        method: "POST",
        data: JSON.stringify(post_data),
        url: matrx_url + ":" + port + "/" + type,
        contentType: "application/json; charset=utf-8",
        dataType: 'json'
    });
}

/*********************************************************************
 * Agent menu
 ********************************************************************/

/**
 * Populate the menu with links to the views of all agents
 */
function populate_agent_menu(state) {
    agents = [];
    var dropdown = document.getElementById("agent_dropdown");

    // remove old agents
    while (dropdown.firstChild) {
        dropdown.removeChild(dropdown.firstChild);
    }


    // search for agents
    var objects_keys = Object.keys(state);
    objects_keys.forEach(function(objID) {
        // don't list ourselves
        if (objID == lv_agent_id) {
            return;
        }

        // fetch agent object from state
        var obj = state[objID];

        // save the agent
        if (obj.hasOwnProperty('isAgent')) {
            agents.push(obj);
        }
    })

    // show what the agent looks like
    agents.forEach(function(agent) {
        var agentType = agent["is_human_agent"] ? "human-agent" : "agent";

        // preview of the agent
        var agent_preview = document.createElement("div");
        agent_preview.classList.add("agent_menu_preview");

        // use the image as the agent preview
        if (Object.keys(agent).includes('img_name')) {
            var img = new Image();
            img.src = window.location.origin + fix_img_url(agent['img_name']);
            agent_preview.append(img);

            // otherwise, use the the agent shape and colour as a preview
        } else {

            // add the css for the corresponding agent shape
            switch (agent['visualization']['shape']) {
                case 0:
                    agent_preview.setAttribute("style", "background-color: " + agent['visualization']['colour'] + ';');
                    break;
                case 2:
                    agent_preview.setAttribute("style", 'background-color:' + agent['visualization']['colour'] + '; border-radius: 100%');
                    break;
                case 1:
                    agent_preview.setAttribute("style", 'width: 0; height: 0; border-left: 15px solid transparent; border-right: 15px solid transparent;border-bottom: 24px solid' + agent['visualization']['colour'] + ';');
                    break;
            }
        }

        // create a new dropdown item and add the preview and agent name
        var list_item = document.createElement('a');
        list_item.classList.add('dropdown-item');
        list_item.append(agent_preview);
        list_item.appendChild(document.createTextNode(agentType + ": " + agent["obj_id"]));
        list_item.href = '/' + agentType + '/' + agent["obj_id"]
        list_item.setAttribute('target', '_blank'); // open in a new tab

        // add the agent to the dropdown list
        dropdown.append(list_item);
    });
}



/*********************************************************************
 * Chat
 ********************************************************************/
var showing_chat = false;
// which chatrooms are added and have a tab
var chatrooms_added = {
    "global": null,
    "team": [],
    "private": []
};
// all the possible chatrooms
var all_chatrooms = {};
// the currently opened chatroom
var current_chatwindow = {
    'name': 'global',
    'type': 'global'
};

/*
 * Add a key listener to the input text box, such that the message will be sent when the user
 * presses enter.
 */
var chat_input_box = document.getElementById("chat_form_input");
if (chat_input_box != null) {
    chat_input_box.addEventListener("keyup", function(event) {
        event.preventDefault();
        if (event.keyCode === 13) {
            document.getElementById("chat_form_submit").click();
        }
    });
}


/*
 * Load the chat rooms when the user clicks the "+" chat room button
 */
function populate_new_chat_dropdown(matrx_chatrooms) {
    all_chatrooms = matrx_chatrooms;

    // get the dropdown from html
    var dropdown = document.getElementById('new_chat_dropdown');

    // remove old items
    while (dropdown.firstChild) {
        dropdown.removeChild(dropdown.firstChild);
    }

    // get chatroom options
    var private_chatroom_options = all_chatrooms['private'].filter(n => !chatrooms_added['private'].includes(n));
    var team_chatroom_options = all_chatrooms['team'].filter(n => !chatrooms_added['team'].includes(n));

    // add private chat room options
    private_chatroom_options.forEach(function(chat_name) {

        // create a new dropdown item and add the preview and agent name
        var list_item = document.createElement('a');
        list_item.classList.add('dropdown-item');
        list_item.classList.add('new_chat_option');
        list_item.appendChild(document.createTextNode(chat_name)); // name
        list_item.chat_name = chat_name;
        list_item.room_type = "private";
        list_item.addEventListener('click', function(event) {
            add_chatroom(event.currentTarget.chat_name, event.currentTarget.room_type);
            open_chatroom(event.currentTarget.chat_name, event.currentTarget.room_type);

            // repopulate the new chat room dropdown
            populate_new_chat_dropdown(all_chatrooms);
        });

        // add the agent to the dropdown list
        dropdown.append(list_item);
    });

    // add team chat room options
    team_chatroom_options.forEach(function(chat_name) {

        // create a new dropdown item and add the preview and agent name
        var list_item = document.createElement('a');
        list_item.classList.add('dropdown-item');
        list_item.classList.add('new_chat_option');
        list_item.appendChild(document.createTextNode(chat_name)); // name
        list_item.chat_name = chat_name;
        list_item.room_type = "team";

        // on click add this chat room
        list_item.addEventListener('click', function(event) {
            add_chatroom(event.currentTarget.chat_name, event.currentTarget.room_type);
            open_chatroom(event.currentTarget.chat_name, event.currentTarget.room_type);

            // repopulate the new chat room dropdown
            populate_new_chat_dropdown(all_chatrooms);
        });

        // add the agent to the dropdown list
        dropdown.append(list_item);
    });
}


/*
 * Hide or show the chat, when the chat button is pressed in the toolbar
 */
function chatToggle() {
    showing_chat = !showing_chat;
    if (showing_chat) {
        document.getElementById("chat_button").className = "btn btn-secondary";
    } else {
        document.getElementById("chat_button").className = "btn btn-dark";
    }
}

/*
 * Add a chat room to the GUI
 */
function add_chatroom(chat_name, room_type, set_active = true) {
    console.log("Adding", room_type, "chatroom:", chat_name);

    // set the previously open chatroom to inactive
    if (set_active) {
        var active_contacts = document.getElementsByClassName("contact_active");
        if (active_contacts.length > 0) {
            active_contacts[0].className = "contact";
        }
    }

    var chatrooms = document.getElementById("chat_rooms_list");
    var global_chatroom = document.getElementById("chatroom_global");

    // create a new item and add the chatroom to the list
    var new_chatroom = document.createElement('div');
    new_chatroom.id = "chatroom_" + chat_name;
    new_chatroom.room_type = room_type;
    new_chatroom.classList.add('contact');
    if (set_active) {
        new_chatroom.classList.add('contact_active'); // set the clicked chatroom to active
    }
    new_chatroom.appendChild(document.createTextNode(chat_name)); // name

    // add a hidden (by default) notification circle, for when new messages have arrived in this
    // chat room while it is unopened
    var chat_room_notification = document.createElement('span');
    chat_room_notification.className = "chat-notification";
    chat_room_notification.id = "chatroom_" + chat_name + "_notification";
    chat_room_notification.style.display = "none";
    new_chatroom.appendChild(chat_room_notification);

    // When the user clicks on an added chat room, open it and display the messages
    new_chatroom.addEventListener('click', chatroom_click);

    // add the new chatroom before the global chatroom
    chatrooms.insertBefore(new_chatroom, global_chatroom);

    // note that we opened this chatroom
    chatrooms_added[room_type].push(chat_name);
}

/*
 * The user clicked on a chatroom, set it as a active and open the chatroom
 */
function chatroom_click(event) {
    // set the previously open chatroom to inactive
    var active_contacts = document.getElementsByClassName("contact_active");
    if (active_contacts.length > 0) {
        active_contacts[0].className = "contact";
    }

    // set this one as active
    event.currentTarget.className = "contact contact_active";

    // open the chatroom
    open_chatroom(event.currentTarget.id, event.currentTarget.room_type);
}


/*
 * Open a chat room and display the messages.
 */
function open_chatroom(chat_room, chat_room_type) {
    // cleanup arguments
    if (chat_room_type == null) {
        chat_room_type = "global";
    }
    chat_room = chat_room.replace("chatroom_", "");

    // set the chat room as selected
    current_chatwindow = {
        'name': chat_room,
        'type': chat_room_type
    };

    console.log("Opening", chat_room_type, "chatroom: ", chat_room);

    // hide the notification of new messages for our goal chat room
    document.getElementById("chatroom_" + chat_room + "_notification").style.display = "none";

    // remove old messages
    var mssgs_container = document.getElementById("messages");
    while (mssgs_container.firstChild) {
        mssgs_container.removeChild(mssgs_container.firstChild);
    }

    // display messages of this chat room, if any
    if (Object.keys(messages).includes(chat_room)) {
        messages[chat_room].forEach(function(message) {
            add_message(chat_room, message, chat_room_type);
        });
    }
}

/*
 * Add an individual message to the specified chat room
 */
function add_message(chat_room, mssg, type) {
    // cleanup and validate the input
    mssg_content = mssg.content.trim();
    if (!mssg_content || mssg_content.length === 0) {
        return;
    }

    var div = document.createElement("div");
    div.className = "message_you"; // by default assume we sent this message

    // check if sent or received this message
    if (mssg.from_id != lv_agent_id) {
        div.className = "message_other";

        // display the sender name if it is a team or global chat message from someone else
        if (type == "global" || type == "team") {
            console.log("adding sender");
            var mssg_sender = document.createElement('span');
            mssg_sender.className = "chat-mssg-sender";
            mssg_sender.appendChild(document.createTextNode(mssg.from_id + ": "));
            div.appendChild(mssg_sender);
        }
    }

    // add the message content
    div.appendChild(document.createTextNode(mssg_content));


    // add the message
    var mssgs_container = document.getElementById("messages");
    mssgs_container.appendChild(div);

    // scroll to the new message
    scrollSmoothToBottom(mssgs_container)
}

/**
 * Scroll smoothly to the end of a div
 */
function scrollSmoothToBottom (div) {
   $(div).animate({
      scrollTop: div.scrollHeight - div.clientHeight
   }, 500);
}

/*
 * Send the message to MATRX
 */
function send_message(event) {
    // get and validate message from input field
    var user_message = document.getElementById("chat_form_input").value;
    user_message = user_message.trim();
    if (!user_message || user_message.length === 0) {
        return;
    }

    // empty input field
    document.getElementById("chat_form_input").value = null;

    // format receiver ID
    var receiver = current_chatwindow['name'] == "global" ? null : current_chatwindow['name'];

    // send message to MATRX
    data = {"content":user_message, "sender": lv_agent_id, "receiver": receiver}
    console.log("Sending message to matrx:", data);
    send_matrx_api_post_message(matrx_send_message_url, data);
}



/*
 * Reset the chat by removing all messages etc.
 */
function reset_chat() {
    // remove the chat room buttons
    chatrooms_added['team'].forEach(function(chat_room) {
        document.getElementById("chatroom_" + chat_room).remove();
    })
    chatrooms_added['private'].forEach(function(chat_room) {
        document.getElementById("chatroom_" + chat_room).remove();
    })

    // remove old messages
    var mssgs_container = document.getElementById("messages");
    while (mssgs_container.firstChild) {
        mssgs_container.removeChild(mssgs_container.firstChild);
    }

    // reset the vars
    chatrooms_added = {
        "global": null,
        "team": [],
        "private": []
    };
    all_chatrooms = {};
    current_chatwindow = {
        'name': 'global',
        'type': 'global'
    };
    messages = {};
}



/*********************************************************************
 * Drawing tools
 ********************************************************************/
// Called when draw button is clicked. Enables/disables draw function
var draw_activated = false;

// Called when erase button is clicked. Enables/disables erase function
var erase_activated = false;

/*
 * Change class of all tiles so that they are highlighted when hovered
 */
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

/*
 * Change class of all tiles so that they are no longer highlighted when hovered
 */
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

/*
 * Toggle drawing mode when the button is pressed
 */
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

/*
 * Toggle erase mode when the button is pressed
 */
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

/*
 * Called when a tile is clicked. Draws/erases the tile and starts drag function that allows the
 * user to draw/erase multiple tiles while holding the left mouse button
 */
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

/*
 * Determines what happens when a tile is selected for drawing / erasing
 */
function drawTile(tile_id) {
    if (draw_activated) {
        var tile = document.getElementById(tile_id);
        tile.style.backgroundColor = "crimson";
    }
}

/*
 * Sets mouse event listeners for drawing  by dragging the mouse
 */
function startDrawDrag() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].setAttribute("onmouseenter", "drawTile(id)");
    }
}

/*
 * Remove the mouse listeners for drawing / erasing by dragging the mouse
 */
function stopDrag() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].setAttribute("onmouseenter", "");
    }
}

/*
 * Determine what happens when a tile is clicked for erasing
 */
function eraseTile(tile_id) {
    if (erase_activated) {
        var tile = document.getElementById(tile_id);
        tile.style.backgroundColor = "";
    }
}

/*
 * Sets mouse event listeners for erasing by dragging the mouse
 */
function startEraseDrag() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].setAttribute("onmouseenter", "eraseTile(id)");
    }
}
