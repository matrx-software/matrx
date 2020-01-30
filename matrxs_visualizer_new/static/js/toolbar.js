
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
