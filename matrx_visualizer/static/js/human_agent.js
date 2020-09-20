/*
 * This file handles keypresses and sends them back to the MATRX server
 */
$(document).ready(function() {
    // bind key listener
    document.onkeydown = check_arrow_key;
});


/**
 * Catch user pressed keys with arrow keys
 *
 */
function check_arrow_key(e) {
    e = e || window.event;

    // ignore the event if the user is writing in the message input field
    if (document.getElementById("chat_form_input") === document.activeElement) {
        return
    }

//    console.log("Userinput:", e);

    data = [e.key];

    send_userinput_to_MATRX(data);
}




function select_agent(e) {


}
