var matrx_url = 'http://' + window.location.hostname,
    port = "3001",
    matrx_context_menu_other = "fetch_context_menu_of_other";
    matrx_context_menu_self = "fetch_context_menu_of_self";

(function ($, window) {

    $.fn.contextMenu = function (settings) {
        return this.each(function () {

            // Open context menu
            $(this).on("contextmenu", function (e) {

                // return native menu if pressing control
                if (e.ctrlKey) return;

                var obj = $(e.target).parent();
                var obj_id = obj.attr('id');
                var x = obj[0].cell_x;
                var y = obj[0].cell_y;

                post_data = {'agent_id_who_clicked': lv_agent_id,
                        'clicked_object_id': obj_id,
                        'click_location': [x,y],
                        'self_selected': object_selected == lv_agent_id,
                        'agent_selected': object_selected}

                // if no one or only ourselves are selected, send to matrx_context_menu_self,
                // otherwise send to matrx_context_menu_other
                var url = ( (!object_selected || post_data['self_selected']) ? matrx_context_menu_self : matrx_context_menu_other);

                var context_menu_request = $.ajax({
                    method: "POST",
                    data: JSON.stringify(post_data),
                    url: matrx_url + ":" + port + "/" + url,
                    contentType: "application/json; charset=utf-8",
                    dataType: 'json'
                });

                // if the request gave an error, print to console and try to reinitialize
                context_menu_request.fail(function(data) {
                    console.log("Context menu request via API failed, response:", data.responseJSON)
                    return false;
                });

                // if the request was succesfull, add the options to the menu and show the menu
                context_menu_request.done(function(data) {
                    // console.log("Context menu request via API successfull, response:", data)

                    var context_menu = $("#contextMenu");

                    // remove all old options
                    context_menu.empty();

                    // add new options
                    data.forEach(function(context_menu_option) {
                        var context_option = document.createElement('a');
                        context_option.className = "dropdown-item";
                        context_option.href= "#";
                        context_option.innerHTML  = context_menu_option.OptionText;
                        context_option.mssg = context_menu_option.Message;

                        // add to the context menu
                        context_menu.append(context_option);
                    });

                    // show the menu in the correct location
                    var $menu = $(settings.menuSelector)
                        .data("invokedOn", $(e.target))
                        .show()
                        .css({
                            position: "absolute",
                            left: getMenuPosition(e.clientX, 'width', 'scrollLeft'),
                            top: getMenuPosition(e.clientY, 'height', 'scrollTop')
                        })
                        .off('click')
                        .on('click', 'a', function (e) {
                            $menu.hide();

                            var $invokedOn = $menu.data("invokedOn");
                            var $selectedMenu = $(e.target);

                            settings.menuSelected.call(this, $invokedOn, $selectedMenu);
                        });
                });

                return false;
            });

            //make sure menu closes on any click
            $('body').click(function () {
                $(settings.menuSelector).hide();
            });
        });

        function getMenuPosition(mouse, direction, scrollDir) {
            var win = $(window)[direction](),
                scroll = $(window)[scrollDir](),
                menu = $(settings.menuSelector)[direction](),
                position = mouse + scroll;

            // opening menu would pass the side of the page
            if (mouse + menu > win && menu < mouse)
                position -= menu;

            return position;
        }

    };
})(jQuery, window);



