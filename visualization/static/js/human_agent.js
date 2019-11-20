/*
 * This file handles keypresses and sends them back to the MATRXS server
 */
$(document).ready(function() {
    // bind key listener
    document.onkeydown = checkArrowKey;
});


/**
 * Catch user pressed keys with arrow keys
 *
 */
function checkArrowKey(e) {
    e = e || window.event;

    console.log("Arrow pressed:", e);

    data = [e.key];

    send_data_to_MATRXS(data);



//    if (e.key === "s") {
//        console.log('set to tick duration of 3s');
//        // send an update for every key pressed
//        var resp = $.ajax({
//            method: "POST",
//            data: JSON.stringify({
//                "message": "Hello",
//                "sender": agent_id,
//                "receiver": ['human_5_120', 'human_7_122']
//            }), // null = None = send to all
//            url: "http://127.0.0.1:3001/send_message",
//            contentType: "application/json; charset=utf-8",
//            dataType: 'json'
//        });
//        console.log("Resp:", resp);
//    }


    //    if (e.key === "q") {
    //        console.log('set to tick duration of 3s');
    //        // send an update for every key pressed
    //        var resp = $.ajax({
    //            method: "GET",
    //            url: "http://127.0.0.1:3001/change_tick_duration/3.0",
    //            contentType:"application/json; charset=utf-8",
    //            dataType: 'json'
    //        });
    //        console.log("Resp:", resp);
    //
    //        // update variables related to tick_duration
    //        tick_duration = 3.0
    //        tps = Math.floor(1.0 / tick_duration);
    //    }

    //    // start
    //    if (e.key === "w") {
    //        console.log('set tot tick duration of 0 seconds ');
    //        // send an update for every key pressed
    //        var resp = $.ajax({
    //            method: "GET",
    //            url: "http://127.0.0.1:3001/change_tick_duration/0",
    //            contentType:"application/json; charset=utf-8",
    //            dataType: 'json'
    //        });
    //        console.log("Resp:", resp);
    //
    //        // update variables related to tick_duration
    //        tick_duration = 0.0
    //        if (tick_duration === 0) {
    //            tick duration = 1.0 / 60;
    //        }
    //        tps = Math.floor(1.0 / tick_duration);
    //    }



}
