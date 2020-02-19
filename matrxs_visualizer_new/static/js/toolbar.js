
// data on the MATRX API
var matrx_url = 'http://' + window.location.hostname,
    port = "3001";


/*********************************************************************
 * Simulation control buttons in toolbar (start/pause etc.)
 ********************************************************************/

// Toolbar elements
var start_button = document.getElementById("start_button"),
    pause_button = document.getElementById("pause_button"),
    stop_button = document.getElementById("stop_button");

/**
 * Synchronizes the play/pause button with the current value of MATRXS
 */
function sync_play_button(matrxs_paused) {
    // hide the play button and show the pause button
    if(!matrxs_paused) {
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
    // hide / unhide the correct button
    start_button.classList.toggle("hidden");
    pause_button.classList.toggle("hidden");

    // send API message to MATRX
    send_api_message("start");
}

pause_button.addEventListener("click", toggle_pause, false);
function toggle_pause() {
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
        contentType:"application/json; charset=utf-8",
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
            img.src = window.location.origin + agent['img_name'];
            agent_preview.append(img);

        // otherwise, use the the agent shape and colour as a preview
        } else {

            // add the css for the corresponding agent shape
            switch(agent['visualization']['shape']) {
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
        list_item.appendChild( document.createTextNode(agentType + ": " + agent["obj_id"]));
        list_item.href = '/' + agentType + '/' + agent["obj_id"]
        list_item.setAttribute('target', '_blank'); // open in a new tab

        // add the agent to the dropdown list
        dropdown.append(list_item);
    });
}



/*********************************************************************
 * Chat
 ********************************************************************/

// which chatrooms are added and have a tab
var chatrooms_added = {"global": null, "team":[], "private":[]};
// all the possible chatrooms
var all_chatrooms = {};
// the currently opened chatroom
var current_chatwindow = {'name': 'global', 'type': 'global'};

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
        list_item.appendChild( document.createTextNode(chat_name)); // name
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
        list_item.appendChild( document.createTextNode(chat_name)); // name
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
 * Add a chat room to the GUI
 */
function add_chatroom(chat_name, room_type) {
    console.log("Adding chatroom ", chat_name, room_type);

    // set the previously open chatroom to inactive
    var active_contacts = document.getElementsByClassName("contact_active");
    if (active_contacts.length > 0) {
        active_contacts[0].className = "contact";
    }

    var chatrooms = document.getElementById("chat_rooms_list");
    var global_chatroom = document.getElementById("chatroom_global");

    // create a new item and add the chatroom to the list
    var new_chatroom = document.createElement('div');
    new_chatroom.id = chat_name;
    new_chatroom.room_type = room_type;
    new_chatroom.classList.add('contact');
    new_chatroom.classList.add('contact_active');    // set the clicked chatroom to active
    new_chatroom.appendChild( document.createTextNode(chat_name)); // name

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
    console.log("Opening chatroom");
    open_chatroom(event.currentTarget.id, event.currentTarget.room_type);
}


/*
 * Open a chat room and display the messages.
 */
function open_chatroom(chat_room, chat_room_type) {
    current_chatwindow = {'name': chat_room, 'type': chat_room_type};

    // remove old messages
    var messages = document.getElementById("messages");
    while (messages.firstChild) {
        messages.removeChild(messages.firstChild);
    }

    // display messages of this chat room, if any
    if (Object.keys(messages).includes(chat_room)) {
        messages[chat_room].forEach(function(message) {
            add_message(chat_room, message);
        });
    }
}

/*
 * Add an individual message to the specified chat room
 */
function add_message(chat_room, mssg) {
    mssg_content = mssg.content.trim()
    console.log("Adding message:", mssg_content, " from ", mssg.from_id, " to ", mssg.to_id);

    if (!mssg_content || mssg_content.length === 0) {
        return;
    }

    var div = document.createElement("div");
    div.innerHTML = mssg_content;
    div.className = "message_you"; // by default assume we sent this message

    // check if sent or received this message
    if (mssg.from_id != lv_agent_id) {
        div.className = "message_other";
    }

    // add the message
    var mssgs_container = document.getElementById("messages");
    mssgs_container.insertBefore(div, mssgs_container.firstChild);
    // document.getElementById("message_input").value = null;
}


/*
 * Reset the chat by removing all messages etc.
 */
function reset_chat() {
    // remove the chat room buttons
    chatrooms_added['team'].forEach(function( chat_room) {
        document.getElementById(chat_room).remove();
    })
    chatrooms_added['private'].forEach(function( chat_room) {
        document.getElementById(chat_room).remove();
    })

    // remove old messages
    var messages = document.getElementById("messages");
    while (messages.firstChild) {
        messages.removeChild(messages.firstChild);
    }

    // reset the vars
    chatrooms_added = {"global": null, "team":[], "private":[]};
    all_chatrooms = {};
    current_chatwindow = {'name': 'global', 'type': 'global'};
    messages = {};
}
