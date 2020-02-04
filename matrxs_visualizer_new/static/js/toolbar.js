
// data on the MATRX API
var matrx_url = "http://127.0.0.1"
var port = "3001"

// Toolbar elements
var start_button = document.getElementById("start_button");
var pause_button = document.getElementById("pause_button");
var stop_button = document.getElementById("stop_button");


start_button.addEventListener("click", toggle_start, false);
function toggle_start() {
    console.log("toggle start");
    // hide / unhide the correct button
    start_button.classList.toggle("hidden");
    pause_button.classList.toggle("hidden");

    // send API message to MATRX
    send_api_message("pause");
}

pause_button.addEventListener("click", toggle_pause, false);
function toggle_pause() {
    console.log("toggle pause");
    // hide / unhide the correct button
    start_button.classList.toggle("hidden");
    pause_button.classList.toggle("hidden");

    // send API message to MATRX
    send_api_message("start");
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
function populate_agent_menu(state, id) {
    console.log("Populating menu with data:", id, state);

    // Hide the menu from people who are not eligible to see it
    if(id != "god" || !state[id].hasOwnProperty('has_menu')) {
        return false;
    }

    agents = [];

    // search for agents
    var objects = Object.keys(state[vis_depth]);
    objects.forEach(function(objID) {
        // don't list ourselves
        if (objID == id) {
            return
        }

        // fetch agent object from state
        var agent = state[vis_depth][objID];

        // save the agent
        if (agent.hasOwnProperty('isAgent')) {
            agents.push(obj);
        }
    })


    var dropdown = document.getElementById("agent_dropdown");

    // show what the agent looks like
    agents.forEach(function(agent) {
        var agentType = agent["is_human_agent"] ? "human-agent" : "agent";



        var newLi = $("<li>").append(
            $('<a>').attr('href', '/' + agentType + '/' + agent["obj_id"]).append($('<div>').attr('class', 'textMenuDiv').append(agent["name"] + " " + agent["obj_id"])));

        switch(agent['visualization']['shape']) {
            case 'img':
                var img = new Image();
                img.src = window.location.origin + agent['img_name'];
                newLi.append($('<div>').attr('class', 'imageMenuDiv').append(img));
                break;
            case 0:
                newLi.append($('<div>').attr('class', 'imageMenuDiv').attr('style', 'background-color:' + agent['visualization']['colour'] + ';'));
                break;
            case 2:
                newLi.append($('<div>').attr('class', 'imageMenuDiv').attr('style', 'background-color:' + agent['visualization']['colour'] + '; border-radius: 100%'))
                break;
            case 1:
                newLi.append($('<div>').attr('class', 'imageMenuDiv').attr('style', 'width: 0; height: 0; border-left: 15px solid transparent; border-right: 15px solid transparent;border-bottom: 24px solid' + agent['visualization']['colour'] + ';'))
                break;
        }
        $("#ListAgents").append(newLi);
    })
    if (!showMenu) {
        $(".menuButton").hide();
    }
}
