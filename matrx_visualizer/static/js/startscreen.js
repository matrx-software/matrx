var ss_update_url = 'http://127.0.0.1:3001/get_latest_state/';

var ss_state = null,
    ss_world_settings = null,
    ss_new_world_ID = null,
    ss_tick_duration = null,
    ss_tps = null;

/*
 * Once the page has loaded, call the initialization functions
 */
$(document).ready(function() {
    ss_fetch_MATRX_state();
});


function ss_fetch_MATRX_state() {

    console.log("Fetching MATRX state");
    // Fetch the latest MATRX state via the API
    var ss_update_request = jQuery.getJSON(ss_update_url + "['god']");

    // if succesfull, save the state and initialize the start screen
    ss_update_request.done(function(data) {
        console.log("Succesfully fetched MATRX state:", data);
        // parse the state info
        ss_state = data[data.length - 1]['god']['state'];
        ss_world_settings = ss_state['World'];
        ss_new_world_ID = ss_state['World']['world_ID'];
        ss_tick_duration = ss_state['World']['tick_duration'];
        ss_tps = (1.0 / ss_tick_duration).toFixed(1); // round to 1 decimal behind the dot

        // populate the agent menu
        ss_populate_agent_menu(ss_state);
    });

    // if the request gave an error, print to console and try again in some time
    ss_update_request.fail(function(data) {
        console.log("Could not connect to MATRX API.");
        console.log("Provided error:", data.responseJSON)

        setTimeout(function() {
            ss_fetch_MATRX_state();
        }, 500);
    });

}


/**
 * Populate the menu with links to the views of all agents
 */
function ss_populate_agent_menu(state) {
    agents = [];
    var dropdown = document.getElementById("view_mode");

    // remove old agents
    while (dropdown.firstChild) {
        dropdown.removeChild(dropdown.firstChild);
    }

    // search for agents
    var objects_keys = Object.keys(state);
    objects_keys.forEach(function(objID) {
        // fetch agent object from state
        var obj = state[objID];

        // save the agent
        if (obj.hasOwnProperty('isAgent')) {
            agents.push(obj);
        }
    })

    // preview of the god view
    var god_preview = document.createElement("div");
    god_preview.classList.add("agent_menu_preview");

    // Set god icon
    var god_icon = new Image();
    god_icon.src = window.location.origin + "/static/images/god.png";
    god_preview.append(god_icon);

    // add god view to the list
    var list_item = document.createElement('a');
    list_item.classList.add('dropdown-item');
    list_item.append(god_preview);
    list_item.appendChild( document.createTextNode('God'));
    list_item.href = '/god'
    list_item.setAttribute('target', '_blank'); // open in a new tab

    // add the agent to the dropdown list
    dropdown.append(list_item);

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
            switch(agent['visualization']['shape']) {
                case 0:
                    agent_preview.setAttribute("style", "background-color: " + agent['visualization']['colour'] + ';');
                    break;
                case 2:
                    agent_preview.setAttribute("style", 'background-color:' + agent['visualization']['colour'] + '; border-radius: 100%');
                    break;
                case 1:
                    agent_preview.setAttribute("style", 'width: 0; height: 0; border-left: 17px solid transparent; border-right: 17px solid transparent;border-bottom: 30px solid' + agent['visualization']['colour'] + ';');
                    break;
            }
        }

        // create a new dropdown item and add the preview and agent name
        var list_item = document.createElement('a');
        list_item.classList.add('dropdown-item');
        list_item.append(agent_preview);
        list_item.appendChild( document.createTextNode(agent["obj_id"]));
        list_item.href = '/' + agentType + '/' + agent["obj_id"]
        list_item.setAttribute('target', '_blank'); // open in a new tab

        // add the agent to the dropdown list
        dropdown.append(list_item);
    });
}


/**
 * Open the agent view in a new tab
 */
function run() {
    var view_mode = document.getElementById("view_mode").value;
    var view_page = view_mode + ".html";
    window.location.href = view_page;
}
