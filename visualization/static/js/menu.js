$(document).ready(function() {
    $(".cross").hide();
    $(".menu").hide();
    $(".hamburger").click(function() {
        $(".menu").slideToggle("slow", function() {
            $(".hamburger").hide();
            $(".cross").show();
        });
    });

    $(".cross").click(function() {
        $(".menu").slideToggle("slow", function() {
            $(".cross").hide();
            $(".hamburger").show();
        });
    });
});

function populateMenu(state, id) {
    console.log("Populating menu with data:", id, state);

    agents = [];
    showMenu = false;
    if ( id === 'god') {
        showMenu = true;
    }

    // loop through the objects and save all agents
    var vis_depths = Object.keys(state);
    vis_depths.forEach(function(vis_depth) {
        var objects = Object.keys(state[vis_depth]);
        objects.forEach(function(objID) {
            // fetch object
            obj = state[vis_depth][objID]

            // save the agent and also (if it is the current agent) if the menu needs to be shown
            if (obj.hasOwnProperty('isAgent')) {
                if (objID == id && obj.hasOwnProperty('has_menu')) {
                        showMenu = obj['has_menu']
                }
                agents.push(obj);
            }
        })
    })

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
