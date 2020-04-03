"""
    Author:         Aaron MacDonald
    Date:           June 14, 2007

    Description:    An implementation of the precise permissive field
                    of view algorithm for use in tile-based games.
                    Based on the algorithm presented at
                    http://roguebasin.roguelikedevelopment.org/index.php?title=Precise_Permissive_Field_of_View.
"""

import copy


def _field_of_view(start_x, start_y, map_width, map_height, radius, func_visit_tile, func_tile_blocked):
    """
    You are free to use or modify this code as long as this notice is
    included.
    This code is released without warranty.

    Determines which coordinates on a 2D grid are visible from a
    particular coordinate.

    startX, startY:         The (x, y) coordinate on the grid that
                            is the centre of view.

    mapWidth, mapHeight:    The maximum extents of the grid.  The
                            minimum extents are assumed to be both
                            zero.

    radius:                 How far the field of view may extend
                            in either direction along the x and y
                            axis.

    funcVisitTile:          User function that takes two integers
                            representing an (x, y) coordinate.  Is
                            used to "visit" visible coordinates.

    funcTileBlocked:        User function that takes two integers
                            representing an (x, y) coordinate.
                            Returns True if the coordinate blocks
                            sight to coordinates "behind" it.
    """

    visited = set()  # Keep track of what tiles have been visited so
    # that no tile will be visited twice.

    # Will always see the centre.
    func_visit_tile(start_x, start_y)
    visited.add((start_x, start_y))

    # Ge the dimensions of the actual field of view, making
    # sure not to go off the map or beyond the radius.

    if start_x < radius:
        min_extent_x = start_x
    else:
        min_extent_x = radius

    if map_width - start_x - 1 < radius:
        max_extent_x = map_width - start_x - 1
    else:
        max_extent_x = radius

    if start_y < radius:
        min_extent_y = start_y
    else:
        min_extent_y = radius

    if map_height - start_y - 1 < radius:
        max_extent_y = map_height - start_y - 1
    else:
        max_extent_y = radius

    # Northeast quadrant
    __check_quadrant(visited, start_x, start_y, 1, 1, max_extent_x, max_extent_y, func_visit_tile, func_tile_blocked)

    # Southeast quadrant
    __check_quadrant(visited, start_x, start_y, 1, -1,
                     max_extent_x, min_extent_y,
                     func_visit_tile, func_tile_blocked)

    # Southwest quadrant
    __check_quadrant(visited, start_x, start_y, -1, -1,
                     min_extent_x, min_extent_y,
                     func_visit_tile, func_tile_blocked)

    # Northwest quadrant
    __check_quadrant(visited, start_x, start_y, -1, 1,
                     min_extent_x, max_extent_y,
                     func_visit_tile, func_tile_blocked)


# -------------------------------------------------------------

class __Line(object):
    def __init__(self, xi, yi, xf, yf):
        self.xi = xi
        self.yi = yi
        self.xf = xf
        self.yf = yf

    dx = property(fget=lambda self: self.xf - self.xi)
    dy = property(fget=lambda self: self.yf - self.yi)

    def p_below(self, x, y):
        return self.relative_slope(x, y) > 0

    def p_below_or_collinear(self, x, y):
        return self.relative_slope(x, y) >= 0

    def p_above(self, x, y):
        return self.relative_slope(x, y) < 0

    def p_above_or_collinear(self, x, y):
        return self.relative_slope(x, y) <= 0

    def p_collinear(self, x, y):
        return self.relative_slope(x, y) == 0

    def line_collinear(self, line):
        return self.p_collinear(line.xi, line.yi) \
               and self.p_collinear(line.xf, line.yf)

    def relative_slope(self, x, y):
        return (self.dy * (self.xf - x)) \
               - (self.dx * (self.yf - y))


class __ViewBump:
    def __init__(self, x, y, parent):
        self.x = x
        self.y = y
        self.parent = parent


class __View:
    def __init__(self, shallow_line, steep_line):
        self.shallow_line = shallow_line
        self.steep_line = steep_line

        self.shallow_bump = None
        self.steep_bump = None


def __check_quadrant(visited, start_x, start_y, dx, dy,
                     extent_x, extent_y, func_visit_tile, func_tile_blocked):
    active_views = []

    shallow_line = __Line(0, 1, extent_x, 0)
    steep_line = __Line(1, 0, 0, extent_y)

    active_views.append(__View(shallow_line, steep_line))
    view_index = 0

    # Visit the tiles diagonally and going outwards
    #
    # .
    # .
    # .           .
    # 9        .
    # 5  8  .
    # 2  4  7
    # @  1  3  6  .  .  .
    max_i = extent_x + extent_y
    i = 1
    while i != max_i + 1 and len(active_views) > 0:
        if 0 > i - extent_x:
            start_j = 0
        else:
            start_j = i - extent_x

        if i < extent_y:
            max_j = i
        else:
            max_j = extent_y

        j = start_j
        while j != max_j + 1 and view_index < len(active_views):
            x = i - j
            y = j
            __visit_coord(visited, start_x, start_y, x, y, dx, dy,
                          view_index, active_views,
                          func_visit_tile, func_tile_blocked)

            j += 1

        i += 1


def __visit_coord(visited, start_x, start_y, x, y, dx, dy, view_index,
                  active_views, func_visit_tile, func_tile_blocked):
    # The top left and bottom right corners of the current coordinate.
    top_left = (x, y + 1)
    bottom_right = (x + 1, y)

    while view_index < len(active_views) \
            and active_views[view_index].steep_line.p_below_or_collinear(bottom_right[0], bottom_right[1]):
        # The current coordinate is above the current view and is
        # ignored.  The steeper fields may need it though.
        view_index += 1

    if view_index == len(active_views) \
            or active_views[view_index].shallow_line.p_above_or_collinear(top_left[0], top_left[1]):
        # Either the current coordinate is above all of the fields
        # or it is below all of the fields.
        return

    # It is now known that the current coordinate is between the steep
    # and shallow lines of the current view.

    is_blocked = False

    # The real quadrant coordinates
    real_x = x * dx
    real_y = y * dy

    if (start_x + real_x, start_y + real_y) not in visited:
        visited.add((start_x + real_x, start_y + real_y))
        func_visit_tile(start_x + real_x, start_y + real_y)
    """else:
        # Debugging
        print (start_x + real_x, start_y + real_y)"""

    is_blocked = func_tile_blocked(start_x + real_x, start_y + real_y)

    if not is_blocked:
        # The current coordinate does not block sight and therefore
        # has no effect on the view.
        return

    if active_views[view_index].shallow_line.p_above(bottom_right[0], bottom_right[1]) \
            and active_views[view_index].steep_line.p_below(top_left[0], top_left[1]):
        # The current coordinate is intersected by both lines in the
        # current view.  The view is completely blocked.
        del active_views[view_index]
    elif active_views[view_index].shallow_line.p_above(
            bottom_right[0], bottom_right[1]):
        # The current coordinate is intersected by the shallow line of
        # the current view.  The shallow line needs to be raised.
        __add_shallow_bump(top_left[0], top_left[1],
                           active_views, view_index)
        __check_view(active_views, view_index)
    elif active_views[view_index].steep_line.p_below(
            top_left[0], top_left[1]):
        # The current coordinate is intersected by the steep line of
        # the current view.  The steep line needs to be lowered.
        __add_steep_bump(bottom_right[0], bottom_right[1], active_views,
                         view_index)
        __check_view(active_views, view_index)
    else:
        # The current coordinate is completely between the two lines
        # of the current view.  Split the current view into two views
        # above and below the current coordinate.

        shallow_view_index = view_index
        view_index += 1
        steep_view_index = view_index

        active_views.insert(shallow_view_index, copy.deepcopy(active_views[shallow_view_index]))

        __add_steep_bump(bottom_right[0], bottom_right[1],
                         active_views, shallow_view_index)
        if not __check_view(active_views, shallow_view_index):
            view_index -= 1
            steep_view_index -= 1

        __add_shallow_bump(top_left[0], top_left[1], active_views,
                           steep_view_index)
        __check_view(active_views, steep_view_index)


def __add_shallow_bump(x, y, active_views, view_index):
    active_views[view_index].shallow_line.xf = x
    active_views[view_index].shallow_line.yf = y

    active_views[view_index].shallow_bump = __ViewBump(x, y, active_views[view_index].shallow_bump)

    cur_bump = active_views[view_index].steep_bump
    while cur_bump is not None:
        if active_views[view_index].shallow_line.p_above(cur_bump.x, cur_bump.y):
            active_views[view_index].shallow_line.xi = cur_bump.x
            active_views[view_index].shallow_line.yi = cur_bump.y

        cur_bump = cur_bump.parent


def __add_steep_bump(x, y, active_views, view_index):
    active_views[view_index].steep_line.xf = x
    active_views[view_index].steep_line.yf = y

    active_views[view_index].steep_bump = __ViewBump(x, y, active_views[view_index].steep_bump)

    cur_bump = active_views[view_index].shallow_bump
    while cur_bump is not None:
        if active_views[view_index].steep_line.p_below(cur_bump.x, cur_bump.y):
            active_views[view_index].steep_line.xi = cur_bump.x
            active_views[view_index].steep_line.yi = cur_bump.y

        cur_bump = cur_bump.parent


def __check_view(active_views, view_index):
    """
        Removes the view in active_views at index view_index if
            - The two lines are coolinear
            - The lines pass through either extremity
    """

    shallow_line = active_views[view_index].shallow_line
    steep_line = active_views[view_index].steep_line

    if shallow_line.line_collinear(steep_line) and (shallow_line.p_collinear(0, 1) or shallow_line.p_collinear(1, 0)):
        del active_views[view_index]
        return False
    else:
        return True
