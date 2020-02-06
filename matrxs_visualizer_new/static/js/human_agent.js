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

}
