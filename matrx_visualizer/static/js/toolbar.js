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
var active_chatrooms = [];
// all the possible chatrooms
var all_chatrooms = {};
// offsets of the latest messages for each chatroom
var chat_offsets = {};
// the currently opened chatroom
var current_chatwindow = {};
// our database with messages, indexed by chat room name
var messages = {};

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
 * Show the chatrooms which the user can open when the user clicks the "+"
 * chatroom button
 */
function populate_new_chat_dropdown(matrx_chatrooms) {
//    console.log("Repopulating new chat dropdown");
    // add to our chatroom database
    all_chatrooms = matrx_chatrooms;

    // get the dropdown from html
    var dropdown = document.getElementById('new_chat_dropdown');

    // remove old items
    while (dropdown.firstChild) {
        dropdown.removeChild(dropdown.firstChild);
    }

    // check if there are any new chatrooms that have to be added to the
    // dropdown chatroom list
    Object.keys(matrx_chatrooms).forEach(function(chatroom_ID) {

        // skip already active chatrooms
        if (active_chatrooms.includes(chatroom_ID)) {
            return;
        }

        chatroom = matrx_chatrooms[chatroom_ID];

        // create a new dropdown item and add the chatroom name
        var list_item = document.createElement('a');
        list_item.classList.add('dropdown-item');
        list_item.classList.add('new_chat_option');
        list_item.id = "new_chatroom_option_" + chatroom_ID;
        list_item.chat_name = chatroom['name'];
        list_item.chatroom_display_name = get_chatroom_display_name(chatroom);
        list_item.appendChild(document.createTextNode(list_item.chatroom_display_name)); // name
        list_item.chatroom_ID = chatroom_ID;
        list_item.room_type = chatroom['type'];

        // on click add this chat room
        list_item.addEventListener('click', function(event) {

            add_chatroom(event.currentTarget.chat_name, event.currentTarget.chatroom_display_name,
                event.currentTarget.chatroom_ID, event.currentTarget.room_type);
            open_chatroom(event.currentTarget.chatroom_display_name, event.currentTarget.chatroom_ID,
                event.currentTarget.room_type);

            // remove this chat from the new chat dropdown
            document.getElementById(event.currentTarget.id).remove();
        });

        // add the chatroom to the dropdown list
        dropdown.append(list_item);
//        console.log("added item to list");
    });
}


/*
 * Get the name that should be displayed for a chatroom in the dropdown / chatroom list
 */
function get_chatroom_display_name(chatroom) {
    // by default the display name is the same as the chatroom name
    var display_name = chatroom['name'];

    // special care for the displayed name of private chats. These chatroom names are in the
    // form of agentID1__agentID2. However that is not a very useful or nice chatroom name.
    // So we remove our own agent ID from the name
    if (chatroom['type'] == "private" && !(lv_agent_id == "god")) {
        // split the chatroom name at the double underscore agent ID divider
        var chat_agent_IDs = chatroom['name'].split("__");

        // agents can send messages to themselves, display it as such
        if (chat_agent_IDs[0] == chat_agent_IDs[1]) {
            return "messages to self"
        }

        // in a private chat with someone else, only display the ID of the other
        chat_agent_IDs.forEach(function(id) {
            if (id != lv_agent_id) {
                display_name = id;
            }
        });
    }

    return display_name
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
 * Add the chatroom to the visible chatrooms
 */
function add_chatroom(chat_name, chatroom_display_name, chatroom_ID, room_type, set_active = true) {
//    console.log("Adding", room_type, "chatroom:", chat_name, "chatroom_display_name:", chatroom_display_name,
//        "chatID:", chatroom_ID);

    // add a new list that will keep track of the messages of this chatroom
    messages[chatroom_ID] = [];

    // set the offset to the first message
    chat_offsets[chatroom_ID] = null;

    // set the previously open chatroom to inactive
    if (set_active) {
        var active_contacts = document.getElementsByClassName("contact_active");
        if (active_contacts.length > 0) {
            active_contacts[0].className = "contact";
        }
    }

    var chatrooms = document.getElementById("chatrooms_list");
    var new_chat_button = document.getElementById("new_chat_button");

    // create a new item and add the chatroom to the list
    var new_chatroom = document.createElement('div');
    new_chatroom.chatroom_ID = chatroom_ID;
    new_chatroom.id = "chatroom_listitem_" + chatroom_ID;
    new_chatroom.room_type = room_type;
    new_chatroom.name = chat_name;
    new_chatroom.chatroom_display_name = chatroom_display_name;
    new_chatroom.classList.add('contact');
    if (set_active) {
        new_chatroom.classList.add('contact_active'); // set the clicked chatroom to active
    }
    new_chatroom.appendChild(document.createTextNode(chatroom_display_name)); // name

    // add a hidden (by default) notification circle, for when new messages have arrived in this
    // chat room while it is unopened
    var chatroom_notification = document.createElement('span');
    chatroom_notification.className = "chat-notification";
    chatroom_notification.id = "chatroom_" + chatroom_ID + "_notification";
    chatroom_notification.style.display = "none";
    new_chatroom.appendChild(chatroom_notification);

    // When the user clicks on an added chat room, open it and display the messages
    new_chatroom.addEventListener('click', chatroom_click);

    // add the new chatroom before the global chatroom
    chatrooms.insertBefore(new_chatroom, new_chat_button);

    // note that we opened this chatroom
    active_chatrooms.push(chatroom_ID);
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
    open_chatroom(event.currentTarget.chatroom_display_name, event.currentTarget.chatroom_ID,
        event.currentTarget.room_type);
}


/*
 * Open a chat room and display the messages.
 */
function open_chatroom(chatroom_display_name, chatroom_ID, chatroom_type) {
    // cleanup arguments
    if (chatroom_type == null) {
        chatroom_type = "global";
    }

    // set the chat room as selected
    current_chatwindow = {
        'chatroom_ID': chatroom_ID,
        'name': chatroom_display_name,
        'type': chatroom_type,
        'receiver': null // by default null = addressed to everyone
    };

    // set the receiver for team and private messages
    if (chatroom_type == 'private' || chatroom_type == 'team') {
        current_chatwindow['receiver'] = chatroom_display_name;
    }

//    console.log("Opening", chatroom_type, "chatroom: ", all_chatrooms[chatroom_ID]['name'], " displayed as ",
//            chatroom_display_name, " with ID ", chatroom_ID);

    // hide the notification of new messages for our goal chat room
    document.getElementById("chatroom_" + chatroom_ID + "_notification").style.display = "none";

    // remove messages from the old chatroom
    var mssgs_container = document.getElementById("messages");
    while (mssgs_container.firstChild) {
        mssgs_container.removeChild(mssgs_container.firstChild);
    }

    // display messages of this chatroom, if any
    if (Object.keys(messages).includes(chatroom_ID)) {
        messages[chatroom_ID].forEach(function(message) {
            add_message(chatroom_ID, message);
        });
    }
}

/*
 * Add 1 message to the currently opened chatroom
 */
function add_message(chatroom_ID, mssg) {
    mssg_content = "";
    // cleanup and validate the input
    if (typeof mssg.content == "string") {
        mssg_content = mssg.content.trim();
    }
    // show objects as strings by default
    else {
        mssg_content = JSON.stringify(mssg.content);
    }

    var div = document.createElement("div");
    div.className = "message_you"; // by default assume we sent this message

    // check if sent or received this message
    if (mssg.from_id != lv_agent_id) {
        div.className = "message_other";

        // display the sender name
        // console.log("adding sender");
        var mssg_sender = document.createElement('span');
        mssg_sender.className = "chat-mssg-sender";
        mssg_sender.appendChild(document.createTextNode(mssg.from_id + ": "));
        div.appendChild(mssg_sender);
    }

    // add the message text to the message div
    div.appendChild(document.createTextNode(mssg_content));

    // add the message div
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

    // send message to MATRX
    data = {"content":user_message, "sender": lv_agent_id, "receiver": current_chatwindow['receiver']}
    console.log("Sending message to matrx:", data);
    send_matrx_api_post_message(matrx_send_message_url, data);
}



/*
 * Reset the chat by removing all messages etc.
 */
function reset_chat() {
    // remove the chat room buttons
    active_chatrooms.forEach(function(chatroom_ID) {
        document.getElementById("chatroom_" + chatroom_ID).remove();
    });

    // remove old messages
    var mssgs_container = document.getElementById("messages");
    while (mssgs_container.firstChild) {
        mssgs_container.removeChild(mssgs_container.firstChild);
    }

    // reset the vars
    active_chatrooms = [];
    all_chatrooms = {};
    chat_offsets = {};
    current_chatwindow = {};
    messages = {};
}


/*
 * Process the object containing messages of various types, received from MATRX, and process them
 * into individual messages.
 */
function process_messages(new_messages, chatrooms) {
    // the messages are in a object with as key the chatroom ID in which they belong
    // Process the new messages for each chatroom
    Object.keys(new_messages).forEach(function(chatroom_ID) {

        // skip any chatrooms without messages
        if (new_messages[chatroom_ID].length == 0) {

            // repopulate the chatroom dropdown if it is new
            if (!Object.keys(all_chatrooms).includes(chatroom_ID)) {
                populate_new_chat_dropdown(chatrooms);
            }
            // skip any further processing
            return
        }

        // add the chatroom to the active chat list if it is new and contains messages
        if (!active_chatrooms.includes(chatroom_ID)) {
            // fetch the chatroom data
            chatroom = chatrooms[chatroom_ID];
//            console.log("adding chatroom", chatroom);

            // add the chatroom to our GUI (but don't show it yet)
            var chatroom_display_name = get_chatroom_display_name(chatroom);
            add_chatroom(chatroom['name'], chatroom_display_name, chatroom_ID, chatroom['type'], set_active=false);

            // repopulate the chatroom dropdown
            populate_new_chat_dropdown(chatrooms);
//            console.log("all chatrooms:", all_chatrooms);
        }

        // fetch the messages for this chatroom
        new_chatroom_mssgs = new_messages[chatroom_ID]

        // the chatroom is currently active, so add and show the new messages
        if (current_chatwindow['chatroom_ID'] == chatroom_ID) {

            // add each message to our database and the GUI
            new_chatroom_mssgs.forEach(function(mssg) {
                mssg = jQuery.parseJSON(mssg);
                chat_offsets[chatroom_ID] = mssg['chat_mssg_count']; // memorize the last mssg index
                messages[chatroom_ID].push(mssg); // add to db
                add_message(chatroom_ID, mssg); // add to GUI
//                console.log("Adding message:", mssg, " type ", all_chatrooms[chatroom_ID]['type'], " chatroom ", all_chatrooms[chatroom_ID]['name']);
//                console.log("Latest message offset is:", mssg['chat_mssg_count']);
            });


        // only add messages to our database but don't show
        } else {
            new_chatroom_mssgs.forEach(function(mssg) {
                mssg = jQuery.parseJSON(mssg);
                chat_offsets[chatroom_ID] = mssg['chat_mssg_count']; // memorize the last mssg index
                messages[chatroom_ID].push(mssg); // add to db
//                console.log("Adding message:", mssg, " type ", all_chatrooms[chatroom_ID]['type'], " chatroom ", all_chatrooms[chatroom_ID]['name']);
//                console.log("Latest message offset (hidden) is:", mssg['chat_mssg_count']);
            })
            if (new_chatroom_mssgs.length != 0 ) {
                // show the notification for the chat room
                document.getElementById("chatroom_" + chatroom_ID + "_notification").style.display = "inline-block";
            }
        }
    });

    // if there is no chat active, set the last chat to active
    if (jQuery.isEmptyObject(current_chatwindow) && active_chatrooms.length != 0) {

        // fetch the last activated chatroom
        chatroom_ID = active_chatrooms[active_chatrooms.length - 1]
        chatroom = all_chatrooms[chatroom_ID];
        // open it
        open_chatroom(get_chatroom_display_name(chatroom), chatroom_ID, chatroom['type'])
        // set it to active
        document.getElementById("chatroom_listitem_" + chatroom_ID).className = "contact contact_active";
    }

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
