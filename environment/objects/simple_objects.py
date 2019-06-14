from environment.objects.env_object import EnvObject
from scenario_manager.helper_functions import get_default_value


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
                         class_callable=SquareBlock)


class Battery(EnvObject):

    def __init__(self, location, name="Battery", start_energy_level=1.0, energy_decay=0.01):
        """
        A simple exanple of an object with an update_properties method that is called each simulation step. It also has
        two default properties that are unique to this object; start_energy_level, and energy_decay. These are added
        as properties by passing them as keyword arguments to the constructor of EnvObject. In addition this constructor
        also makes a current_enery_level attribute which is also treated as a property by giving it to the EnvObject
        constructor as well. All other properties are obtained from the defaults.json as defined for all EnvObject,
        except for the size (which is set to be 0.25) and the colour (which is a shade of green turning to red based on
        the current_energy_level).

        Its update_properties method simply decays the current energy level with the given factor and the colour
        accordingly.

        :param location: The location of the battery.
        :param name: Optional. Defaults to 'Battery'.
        :param start_energy_level: Optional. Defaults to 1.0
        :param energy_decay: Optional. Defaults to 0.01, meaning the energy decreases with 1% of its current value each
        simulation step.
        """

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

    def update_properties(self, grid_world):
        """
        Updates the current energy level, changes the property accordingly, and also change the visualization color.
        :param grid_world: The state of the world. Not used.
        :return: The new properties
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


class Door(EnvObject):

    def __init__(self, location, is_open, name="Door", open_colour="#646464", closed_colour="#191919"):
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

    def __init__(self, location, name="Wall", visualization_colour="#000000"):
        """
        A simple Wall object. Is not traversable, the colour can be set but has otherwise the default EnvObject property
        values.
        :param location: The location of the wall.
        :param name: The name, default "Wall".
        """
        is_traversable = False  # All walls are always not traversable
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         is_traversable=is_traversable, class_callable=Wall)


class Area(EnvObject):

    def __init__(self, location, name="Area", visualization_colour="#8ca58c"):
        """
        A simple Area object. Is always traversable, the colour can be set but has otherwise the default EnvObject
        property values. Can be used to define different areas in the GridWorld.
        :param location: The location of the area.
        :param name: The name, default "Area".
        """
        is_traversable = True  # Areas are always traversables
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         is_traversable=is_traversable, class_callable=Area)

class Brand(EnvObject):

    def __init__(self, location, omvang=None, name="Brand"):
        """
        An incident object...
        :param location: The location of the area.
        :param name: The name, default "Area".
        """
        visualization_colour="#ff3200"
        visualization_depth=6
        visualization_size=0.3

        if omvang=="klein":
            visualization_shape=0
        elif omvang=="middelmatig":
            visualization_shape=1
        elif omvang=="groot":
            visualization_shape=2

        is_traversable = True  # Areas are always traversables
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         visualize_size=visualization_size, visualize_shape=visualization_shape, is_traversable=is_traversable, class_callable=Brand, omvang=omvang, visualize_depth=visualization_depth)

class Lekkage(EnvObject):

    def __init__(self, location, omvang=None, name="Lekkage"):
        """
        An incident object...
        :param location: The location of the area.
        :param name: The name, default "Area".
        """
        visualization_colour="#10cec1"
        visualization_depth=5
        visualization_size=0.4

        if omvang=="klein":
            visualization_shape=1
        if omvang=="middelmatig":
            visualization_shape=2
        if omvang=="groot":
            visualization_shape=0

        is_traversable = True  # Areas are always traversables
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         visualize_size=visualization_size, visualize_shape=visualization_shape, is_traversable=is_traversable, class_callable=Lekkage, omvang=omvang, visualize_depth=visualization_depth)

class Gewonde(EnvObject):

    def __init__(self, location, omvang=None, name="Gewonde"):
        """
        An incident object...
        :param location: The location of the area.
        :param name: The name, default "Area".
        """
        visualization_colour="#11ce24"
        visualization_depth=4
        visualization_size=0.5

        if omvang=="klein":
            visualization_shape=0
        if omvang=="middelmatig":
            visualization_shape=1
        if omvang=="groot":
            visualization_shape=2

        is_traversable = True  # Areas are always traversables
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         visualize_size=visualization_size, visualize_shape=visualization_shape, is_traversable=is_traversable, class_callable=Gewonde, omvang=omvang, visualize_depth=visualization_depth)


class C4I(EnvObject):

    def __init__(self, location, omvang=None, name="C4I"):
        """
        An incident object...
        :param location: The location of the area.
        :param name: The name, default "Area".
        """
        visualization_colour="#1424ce"
        visualization_depth=3
        visualization_size=0.6
        
        if omvang=="klein":
            visualization_shape=0
        if omvang=="middelmatig":
            visualization_shape=1
        if omvang=="groot":
            visualization_shape=2

        is_traversable = True  # Areas are always traversables
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         visualize_size=visualization_size, visualize_shape=visualization_shape, is_traversable=is_traversable, class_callable=C4I, omvang=omvang, visualize_depth=visualization_depth)

class Energy(EnvObject):

    def __init__(self, location, omvang=None, name="Energy"):
        """
        An incident object...
        :param location: The location of the area.
        :param name: The name, default "Area".
        """
        visualization_colour="#ce8013"
        visualization_depth=2
        visualization_size=0.7

        if omvang=="klein":
            visualization_shape=0
        if omvang=="middelmatig":
            visualization_shape=1
        if omvang=="groot":
            visualization_shape=2

        is_traversable = True  # Areas are always traversables
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         visualize_size=visualization_size, visualize_shape=visualization_shape, is_traversable=is_traversable, class_callable=Energy, omvang=omvang, visualize_depth=visualization_depth)


class Mobiliteit(EnvObject):

    def __init__(self, location, omvang=None, name="Mobiliteit"):
        """
        An incident object...
        :param location: The location of the area.
        :param name: The name, default "Area".
        """
        visualization_colour="#892375"
        visualization_depth=1
        visualization_size=0.8
        
        if omvang=="klein":
            visualization_shape=0
        if omvang=="middelmatig":
            visualization_shape=1
        if omvang=="groot":
            visualization_shape=2

        is_traversable = True  # Areas are always traversables
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         visualize_size=visualization_size, visualize_shape=visualization_shape, is_traversable=is_traversable, class_callable=Mobiliteit, omvang=omvang, visualize_depth=visualization_depth)


class SeWaCo(EnvObject):

    def __init__(self, location, omvang=None, name="SeWaCo"):
        """
        An incident object...
        :param location: The location of the area.
        :param name: The name, default "Area".
        """
        visualization_colour="#ce12be"
        visualization_depth=0
        visualization_size=0.9
        
        if omvang=="klein":
            visualization_shape=0
        if omvang=="middelmatig":
            visualization_shape=1
        if omvang=="groot":
            visualization_shape=2

        is_traversable = True  # Areas are always traversables
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         visualize_size=visualization_size, visualize_shape=visualization_shape, is_traversable=is_traversable, class_callable=C4I, omvang=omvang, visualize_depth=visualization_depth)

class Waypoint(EnvObject):

    def __init__(self, location, name="Waypoint", visualization_colour="#8ca58c", route_name="Route", waypoint_number=0):
        """
        An incident object...
        :param location: The location of the area.
        :param name: The name, default "Area".
        """

        visualization_size=0.1
        visualization_shape=1

        is_traversable = True  # Areas are always traversables
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         visualize_size=visualization_size, visualize_shape=visualization_shape, is_traversable=is_traversable, class_callable=Waypoint)

        self.add_property("route_name", route_name)
        self.add_property("waypoint_number", waypoint_number)
