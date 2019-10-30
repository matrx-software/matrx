$(document).ready(function() {
    $(".cross").hide();
    $(".menu").hide();
    $(".hamburger").click(function() {
    $(".menu").slideToggle( "slow", function() {
    $(".hamburger").hide();
    $(".cross").show();
    });
});

$(".cross").click(function() {
    $(".menu").slideToggle( "slow", function() {
    $(".cross").hide();
    $(".hamburger").show();
    });
    });
});

function populateMenu(state, id){
  agents=[];
  showMenu=false;
  if(typeof id =='undefined'){ //it is coming from god view
    showMenu=true
  }
  var vis_depths = Object.keys(state);
  vis_depths.forEach(function(vis_depth)
    {
        var objects = Object.keys(state[vis_depth]);
        objects.forEach(function(objID) {
        // fetch object
        obj = state[vis_depth][objID]

        // fetch location of object in pixel values
        if(obj.hasOwnProperty('isAgent')){
            if(objID==id){
                if(obj.hasOwnProperty('has_menu')){
                    showMenu = obj['has_menu']
                }
            }
            agents.push(obj);
        }
        })
    })
  agents.forEach(function(agent){
      var agentType = agent["is_human_agent"] ? "human-agent" : "agent";
      var newLi=$("<li>").append(
      $('<a>').attr('href','/' + agentType + '/'+ agent["obj_id"]).append($('<div>').attr('class', 'textMenuDiv').append(agent["name"] +" "+ agent["obj_id"])));
      if (agent['visualization']['shape'] == 'img'){
         var img = new Image();
         img.src = window.location.origin + '/static/avatars/'+agent['img_name'];
         newLi.append($('<div>').attr('class', 'imageMenuDiv').append(img))
         }
       else if(agent['visualization']['shape'] == 0) {
                newLi.append($('<div>').attr('class', 'imageMenuDiv').attr('style', 'background-color:'+agent['visualization']['colour']+';'))
            }
        else if(agent['visualization']['shape'] == 2) {
                newLi.append($('<div>').attr('class', 'imageMenuDiv').attr('style', 'background-color:'+agent['visualization']['colour']+'; border-radius: 100%'))
            }
         else if(agent['visualization']['shape'] == 1) {
                newLi.append($('<div>').attr('class', 'imageMenuDiv').attr('style', 'width: 0; height: 0; border-left: 15px solid transparent; border-right: 15px solid transparent;border-bottom: 24px solid'+ agent['visualization']['colour']+';'))
            }


      $("#ListAgents").append(newLi);
    })
    if(!showMenu){
        $(".menuButton").hide();
      }
}
