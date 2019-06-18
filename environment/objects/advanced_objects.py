from environment.objects.env_object import EnvObject


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