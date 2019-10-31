/**
 * This is the file which handles the socketIO connection for the god view,
 * requesting a redraw of the grid when a socketIO update has been received.
 */

 var doVisualUpdates = true;
// var isFirstCall=true;

/**
 * Check if the current tab is in focus or not
 */
document.addEventListener('visibilitychange', function(){
  doVisualUpdates = !document.hidden;
});

//
//function update(progress) {
//  // Update the state of the world for the elapsed time since last render
//}
//
//function draw() {
//  // Draw the state of the world
//}
//
//function loop(timestamp) {
//  var progress = timestamp - lastRender
//
//  update(progress)
//  draw()
//
//  lastRender = timestamp
//  window.requestAnimationFrame(loop)
//}
//var lastRender = 0
//window.requestAnimationFrame(loop)




function init() {
    var url = 'http://localhost:3000/get_info'

    var resp = $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        async: false
    });

    console.log("Complete response:", resp.status);

    if (resp.status != 200) {
        console.log("Oh no, an error");
        return false
    }

    var settings = resp.responseText;
}


function success(data) {
    console.log("Success");
}


$(document).ready(function(){

    init();

//
//    /**
//     * receive an update from the python server
//     */
//    socket.on('update', function(data){
//         console.log("Received an update from the server:", data);
//
//        // Only perform the GUI update if it is in the foreground, as the
//        // background tabs are often throttled after which the browser cannot
//        // keepup
//        if (!doVisualUpdates) {
//            console.log("Chrome in background, skipping");
//            return;
//        }
//
//        // unpack received data
//        grid_size = data.params.grid_size;
//        state = data.state;
//        tick = data.params.tick;
//        vis_bg_clr = data.params.vis_bg_clr;
//        vis_bg_img = data.params.vis_bg_img;
//        //draw the menu if it is the first call
//        if(isFirstCall){
//            isFirstCall=false;
//            populateMenu(state);
//            parseGifs(state);}
//        // draw the grid again
//        requestAnimationFrame(function() {
//            doTick(grid_size, state, tick, vis_bg_clr,vis_bg_img, parsedGifs);
//        });
//    });
});
