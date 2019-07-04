from environment.objects.env_object import EnvObject
from world_factory.helper_functions import get_default_value


class SquareBlock(EnvObject):

    def __init__(self, location, name="Block"):
        """
        An example of a simple object with a set of attributes that are always the same. In this case that it is not
        traversable, and is visualized as a square. Otherwise it takes all default properties from an EnvObject and has
        not other custom properties.
        :param location: Location of the block.
        :param name: The name of the block, if not given it is simply "Block".
        """

        super().__init__(name=name, location=location, is_traversable=False, visualize_shape=0,
                         class_callable=SquareBlock, visualize_opacity=1.0)


class Door(EnvObject):

    def __init__(self, location, is_open, name="Door", open_colour="#006400", closed_colour="#640000"):
        """
        Door base object, can be used to define rooms. An example of an object that is and ordinary EnvObject but has
        a method on which two Actions depend; OpenDoorAction and CloseDoorAction. This method alters the is_traversable
        property accordingly.

        It also has two colors which the
        door visualization changes into when open or closed.

        :param location: Location of door.
        :param name: Name of object, defaults to "Door"
        :param open_colour: Colour when open
        :param closed_colour: Colour when closed
        """

        # Whether the door is by default open or closed is stored in the defaults.json and obtained like this;
        self.is_open = is_open

        # We save the colours for open and close and assign the appriopriate value based on current state
        self.open_colour = open_colour
        self.closed_colour = closed_colour
        current_color = self.closed_colour
        if self.is_open:
            current_color = self.open_colour

        # If the door is open or closed also determines its is_traversable property
        is_traversable = self.is_open

        super().__init__(location=location, name=name, is_traversable=is_traversable, visualize_colour=current_color,
                         is_open=self.is_open, class_callable=Door)

    def open_door(self):
        """
        Opens the door, changes the colour and sets the properties as such.
        """

        # Set the attribute
        self.is_open = True
        # Set the appropriate property
        self.change_property("is_open", self.is_open)
        # Traversable depends on this as well
        self.is_traversable = self.is_open
        # Also change the colour
        self.visualize_colour = self.open_colour

    def close_door(self):
        """
        Closes the door, changes the colour and sets the properties as such.
        """

        # Set the attribute
        self.is_open = False
        # Set the appropriate property
        self.change_property("is_open", self.is_open)
        # Traversable depends on this as well
        self.is_traversable = self.is_open
        # Also change the colour
        self.visualize_colour = self.closed_colour


class Wall(EnvObject):

    def __init__(self, location, name="Wall", visualize_colour="#000000"):
        """
        A simple Wall object. Is not traversable, the colour can be set but has otherwise the default EnvObject property
        values.
        :param location: The location of the wall.
        :param name: The name, default "Wall".
        """
        is_traversable = False  # All walls are always not traversable
        super().__init__(name=name, location=location, visualize_colour=visualize_colour,
                         is_traversable=is_traversable, class_callable=Wall)


class AreaTile(EnvObject):

    def __init__(self, location, name="AreaTile", visualize_colour="#8ca58c", visualize_depth=None, visualize_opacity=1.0):
        """
        A simple AreaTile object. Is always traversable, not movable, the colour can be set but has otherwise the default EnvObject
        property values. Can be used to define different areas in the GridWorld.
        :param location: The location of the area.
        :param name: The name, default "AreaTile".
        :param visualize_colour: hex colour code for tile
        """
        super().__init__(name=name, location=location, visualize_colour=visualize_colour,
                         is_traversable=True, is_movable=False, class_callable=AreaTile,
                         visualize_depth=visualize_depth, visualize_opacity=visualize_opacity)


class SmokeTile(AreaTile):
    def __init__(self, location, name="SmokeTile", visualize_colour="#b7b7b7", visualize_opacity=0.8, visualize_depth=101):
        """
        An object representing one tile of smoke. Is always traversable, not movable,
        and square shaped. Can be transparent.
        :param location: The location of the area.
        :param name: The name, default "SmokeTile".
        :param visualize_colour: hex colour code for tile. default is grey.
        :param visualize_opacity: Opacity of the object. By default 0.8
        :param visualize_depth: depth of visualization. By default 101: just above agent and other objects
        """
        visualize_depth = 101 if visualize_depth is None else visualize_depth
        super().__init__(name=name, location=location, visualize_colour=visualize_colour,
                        visualize_opacity=visualize_opacity, visualize_depth=visualize_depth)
