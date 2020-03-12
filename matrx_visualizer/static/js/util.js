/*
 * Convert the path to an image to the correct url. This depends on if it is a local image file in the MATRX package
 * (url starting with '/static/'), or a local file relative from the users folder in which the user imported MATRX (NOT
 * starting with '/static/').
 */
function fix_img_url(img_name) {

   // check if it is an external media file
   if (!img_name.includes('/static/')) {
        // append the path such that Flask will recognize it as an external media file
        var img_path = "/fetch_external_media/" + img_name;
        // replace any double slashes
        img_path = img_path.replace('//', '/').replace('/\\','/');
        return img_path;
    }

    // otherwise it is an internal image (inside the MATRX visualizer package in the static folder), so nothing has to be fixed
    return img_name;
}