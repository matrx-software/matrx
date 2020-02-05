
// data on the MATRX API
var matrx_url = "http://127.0.0.1"
var port = "3001"

// Toolbar elements
var start_button = document.getElementById("start_button");
var pause_button = document.getElementById("pause_button");
var stop_button = document.getElementById("stop_button");


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

        // use the image as the agent preview
        if (Object.keys(obj).includes('img_name')) {
            var img = new Image();
            img.src = window.location.origin + agent['img_name'];
            agent_preview.append(img);

        // otherwise, use the the agent shape and colour as a preview
        } else {
            agent_preview.classList.add("agent_menu_preview");

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

        // add the agent to the dropdown list
        dropdown.append(list_item);
    });
}
