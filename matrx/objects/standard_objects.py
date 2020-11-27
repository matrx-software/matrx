from matrx.objects.env_object import EnvObject

""" A number of standard, often used objects. """

class SquareBlock(EnvObject):
    """
    An example of a simple object with a set of attributes that are always the same. In this case that it is not
    traversable, and is visualized as a square. Otherwise it takes all default properties from an EnvObject and has
    not other custom properties.

    Parameters
    ----------
    location: tuple
        Location of door.
    name: string. Optional, default "Block"
        Name of block, defaults to "Block"
    **custom_properties:
        Additional properties that should be added to the object.
    """

    def __init__(self, location, name="Block", visualize_colour="#4286f4", **custom_properties):
        super().__init__(name=name, location=location, visualize_shape=0, is_traversable=False,
                         class_callable=SquareBlock, visualize_colour=visualize_colour, **custom_properties)


class Door(EnvObject):
    """
    Door base object, can be used to define rooms. An example of an object that is and ordinary EnvObject but has
    a method on which two Actions depend; OpenDoorAction and CloseDoorAction. This method alters the is_traversable
    property accordingly.

    It also has two colors which the
    door visualization changes into when open or closed.

    Parameters
    ----------
    location: tuple
        Location of door.
    name: string. Optional, default "Door"
        Name of object, defaults to "Door"
    open_colour: string. Optional, default "#006400"
        Colour when open
    closed_colour: string. Optional, default "#640000"
        Colour when closed
    **kwargs:
        Dict of additional properties that should be added to the object as well.
    """
    def __init__(self, location, is_open, name="Door", open_colour="#006400", closed_colour="#640000",
                 **kwargs):

        # Whether the door is by default open or closed is stored in the defaults.py and obtained like this;
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
                         is_open=self.is_open, class_callable=Door, is_movable=False,
                         customizable_properties=['is_open'], **kwargs)

    def open_door(self):
        """ Opens the door, changes the colour and sets the properties as such.
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
        """ Closes the door, changes the colour and sets the properties as such.
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
    """
    A simple Wall object. Is not traversable, the colour can be set but has otherwise the default EnvObject property
    values.

    Parameters
    ----------
    location: tuple
        The location of the wall.
    name: string. Optional, default "Wall"
        The name, default "Wall".
    """
    def __init__(self, location, name="Wall", visualize_colour="#000000", **kwargs):

        is_traversable = False  # All walls are always not traversable
        super().__init__(name=name, location=location, visualize_colour=visualize_colour,
                         is_traversable=is_traversable, class_callable=Wall, is_movable=False,
                         **kwargs)


class AreaTile(EnvObject):
    """
    A simple AreaTile object. Is always traversable, not movable, the colour can be set but has otherwise the
    default EnvObject property values. Can be used to define different areas in the GridWorld.

    Parameters
    ----------
    location: tuple
        The location of the area.
    name: string. Optional, default "AreaTile"
        The name, default "AreaTile".
    visualize_colour: string. Optional, default is "#b7b7b7"
        hex colour code for tile. default is grey.
    visualize_opacity: float. Optional, default 0.8.
        Opacity of the object. By default 0.8
    visualize_depth: int. Optional, default=101
        depth of visualization. By default 101: just above agent and other objects Higher means higher priority.
    **kwargs: Optional.
        Set of additional properties that should be added to the object as well.
    """
    def __init__(self, location, name="AreaTile", visualize_colour="#8ca58c", visualize_depth=None,
                 visualize_opacity=1.0, **kwargs):
        super().__init__(name=name, location=location, visualize_colour=visualize_colour,
                         is_traversable=True, is_movable=False, class_callable=AreaTile,
                         visualize_depth=visualize_depth, visualize_opacity=visualize_opacity,
                         **kwargs)


class SmokeTile(AreaTile):
    """
    An object representing one tile of smoke. Is always traversable, not movable,
    and square shaped. Can be transparent.

    Parameters
    ----------
    location: tuple
        The location of the area.
    name: String. Optiona, default:"SmokeTile"
        The name, default "SmokeTile".
    visualize_colour: string. Optional, default is "#b7b7b7"
        hex colour code for tile. default is grey.
    visualize_opacity: float. Optional, default 0.8.
        Opacity of the object. By default 0.8
    visualize_depth: int. Optional, default=101
        depth of visualization. By default 101: just above agent and other objects Higher means higher priority.
    """
    def __init__(self, location, name="SmokeTile", visualize_colour="#b7b7b7", visualize_opacity=0.8,
                 visualize_depth=101):
        visualize_depth = 101 if visualize_depth is None else visualize_depth
        super().__init__(name=name, location=location, visualize_colour=visualize_colour,
                         visualize_opacity=visualize_opacity, visualize_depth=visualize_depth)


class Battery(EnvObject):
    """
    A simple example of an object with an update_properties method that is called each simulation step. It also has
    two default properties that are unique to this object; start_energy_level, and energy_decay. These are added
    as properties by passing them as keyword arguments to the constructor of EnvObject. In addition this constructor
    also makes a current_enery_level attribute which is also treated as a property by giving it to the EnvObject
    constructor as well. All other properties are obtained from the defaults.py as defined for all EnvObject,
    except for the size (which is set to be 0.25) and the colour (which is a shade of green turning to red based on
    the current_energy_level).

    Its update_properties method simply decays the current energy level with the given factor and the colour
    accordingly.

    Parameters
    ----------
    location: list
        The location of the battery.
    name: String (optional).
        Defaults to 'Battery'.
    start_energy_level: float (optional)
        Defaults to 1.0
    energy_decay: float (optional)
        Defaults to 0.01, meaning the energy decreases with 1% of its current value each simulation step.
    """
    def __init__(self, location, name="Battery", start_energy_level=1.0, energy_decay=0.01):

        self.start_energy_level = start_energy_level
        self.current_energy_level = start_energy_level
        self.energy_decay = energy_decay
        super().__init__(name=name, location=location,
                         visualize_shape=0,  # a battery is always square
                         visualize_size=0.25,  # a battery is always 1/4th of a grid square of the visualization
                         customizable_properties=["current_energy_level"],  # the current energy level can be changed
                         visualize_colour="#32b432",
                         energy_decay=self.energy_decay,
                         current_energy_level=self.current_energy_level,
                         class_callable=Battery)

    def update(self, grid_world):
        """
        Updates the current energy level, changes the property accordingly, and also change the visualization color.

        Parameters
        ----------
        grid_world: Gridworld
            The state of the world. Not used.

        Returns
        -------
        The new properties: Dict
        """

        # Calculate the new energy level
        self.current_energy_level = self.current_energy_level * (1 - self.energy_decay)
        if self.current_energy_level < 0.0001:
            self.current_energy_level = 0

        # Updates the energy level property, if we do not do this the property will not reflect the actual value
        self.change_property(property_name="current_energy_level", property_value=self.current_energy_level)

        # Change the color (we shift from green to red)
        hex_color = self.visualize_colour
        if self.current_energy_level != 0:  # if energy level is not zero.
            new_red = int(50 + 130 * (1 - self.current_energy_level / self.start_energy_level))  # >red as less energy
            new_green = int(50 + 130 * (self.current_energy_level / self.start_energy_level))  # >green, as more energy
            hex_color = '#{:02x}{:02x}{:02x}'.format(new_red, new_green, 50)
        self.visualize_colour = hex_color  # we do not need to set this property, as it is not a custom property

        # Return the properties themselves.
        return self.properties


class CollectionTarget(EnvObject):
    """ An invisible object that tells which objects needs collection.

    This invisible object is linked to `CollectionDropTile` object(s) and is used by the `CollectionGoal` to
    identify which objects should be collected and dropped off at the tiles. This object is just a regular object
    but contains three additional properties:
    - collection_objects: See parameter doc.
    - collection_zone_name: See parameter doc.
    - is_invisible: A boolean denoting that this object is invisible. This boolean has no effect in MATRX, except to
    denote that this object is not an actual visible object.
    - is_drop_off_target: Denotes this object as containing the descriptions of the to be collected objects.

    The invisibility is implemented as a block with full opacity, not movable, fully traversable and always below
    other objects.

    Parameters
    ----------
    location : (x, y)
        The location of this object.
    collection_objects : List of dicts
        A list of dictionaries, each dictionary in this list represents an object that should be dropped at this
        location. The dictionary itself represents the property-value pairs these objects should adhere to. The
        order of the list matters iff the `CollectionGoal.in_order==True`, in which case the
        `CollectionGoal` will track if the dropped objects at this tile are indeed dropped in the order of the list.
    collection_zone_name : str
        This is the name that links `CollectionDropTile` object(s) to this object. The `CollectionGoal` will check
        all of these tiles with this name to check if all objects are already dropped and collected.
    name : str (default is "Collection_target")
        The name of this object.

    Notes
    -----
    It does not matter where this object is added in the world. However, it is good practice to add it on top of
    the (or one of them) `CollectionDropTile` object(s). The helper method to create collection areas
    `WorldBuilder.add_collection_goal` follows this practice.

    See Also
    --------
    matrx.WorldBuilder.add_collection_goal
            The handy method in the `WorldBuilder` to add a collection goal to the world and required object(s).
    matrx.goals.CollectionGoal
        The `CollectionGoal` that performs the logic of check that all object(s) are dropped at the drop off tiles.
    matrx.objects.CollectionDropTile
        The tile that represents the location(s) where the object(s) need to be dropped.
    """
    def __init__(self, location, collection_objects, collection_zone_name, name="Collection_target"):

        super().__init__(location=location, name=name, class_callable=CollectionTarget, customizable_properties=None,
                         is_traversable=True, is_movable=False, visualize_size=0, visualize_shape=0,
                         is_drop_off_target=True, visualize_colour=None, visualize_depth=None, visualize_opacity=0.0,
                         collection_objects=collection_objects, collection_zone_name=collection_zone_name,
                         is_invisible=True)


class CollectionDropOffTile(AreaTile):
    """
    An area tile used to denote where one or more objects should be dropped. It is similar to any other `AreaTile`
    but has two additional properties that identify it as a drop off location for objects and the name of the drop
    off. These are used by a `CollectionGoal` to help find the drop off area in all world objects.

    Parameters
    ----------
    location : (x, y)
        The location of this tile.
    name : str (default is "Collection_zone")
        The name of this tile.
    collection_area_name: str (default is "Collection_zone")
        The name of the collection zone this collection tile belongs to. It is used by the respective CollectionGoal
        to identify where certain objects should be dropped.
    visualize_colour : String (default is "#64a064", a pale green)
        The colour of this tile.
    visualize_opacity : Float (default is 1.0)
        The opacity of this tile. Should be between 0.0 and 1.0.

    See also
    --------
    matrx.WorldBuilder.add_collection_goal
            The handy method in the `WorldBuilder` to add a collection goal to the world and required object(s).
    matrx.goals.CollectionGoal
        The `CollectionGoal` that performs the logic of check that all object(s) are dropped at the drop off tiles.
    matrx.objects.CollectionTarget
        The invisible object representing which object(s) need to be collected and (if needed) in which order.
    """
    def __init__(self, location, name="Collection_zone", collection_area_name="Collection zone",
                 visualize_colour="#64a064", visualize_opacity=1.0, **kwargs):
        super().__init__(location, name=name, visualize_colour=visualize_colour, visualize_depth=None,
                         visualize_opacity=visualize_opacity, is_drop_off=True,
                         collection_area_name=collection_area_name, **kwargs)
