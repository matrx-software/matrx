import inspect
import warnings

from environment.objects.helper_functions import *
from scenario_manager.helper_functions import get_default_value


class EnvObject:

    def __init__(self, location, name, customizable_properties=None,
                 is_traversable=None, carried_by=None,
                 visualize_size=None, visualize_shape=None, visualize_colour=None, **custom_properties):
        """
        The basic class for all objects in the world. This includes the AgentAvatar. All objects that are added to the
        GridWorld should inherit this class.

        An EnvObject always needs a location and a name. Since we have no idea where you want to put the object or how
        you want to call it.

        In addition agents may alter properties of objects, but only if they are specifically told to be customizable.
        This is done by providing a list of property names in the customizable_properties list.
        Any custom property is allowed to be customizable if in that list, but any keyword argument (e.g.
        is_traversable) may only be influenced by an Action indirectly. For example, the is_traversable property cannot
        be changed in any way, whereas the location property can only be changed indirectly through the PickUpObject
        action.

        A few properties are mandatory for the GridWorld, some Actions and the Visualizer to function. These are
        keyword arguments (e.g. is_traversable). If these are not set, they are obtained from the defaults.json file.
        
        This class specific allows you to create any object you desire that only differs in the properties it holds. For
        example both a simple block or complex object such as a 'fire' can be modeled with this class. They only differ
        in their mandatory and custom properties (a block is simply a colored square, whereas a 'fire' has potentially
        many more properties). In such a case you simply provide more keyword arguments to the constructor, these
        are automatically added to the self.custom_attributes dictionary. Allowing you to intuitively extend the
        properties of any EnvObject.

        If you want an object that can be altered by an action in a specific way, you can create it as long as it
        inherits from this class. For example the Door object is such an example which has a unique method that 'opens'
        or 'closes' the door. Which is called by the OpenDoor and CloseDoor actions.

        If you want an object that needs to update some of its own properties during the simulation, you can again
        create your own object as long as it inherits from this class. Then you can implement the update_properties
        method. The Battery object is such an example, which simply decreases its energy level property each time step.

        If you have a specific object you need to create a lot and you do not want to keep on setting every property
        every time for the custom_properties, you can make your own class again which must inherit from this class and
        only implement its constructor where these custom properties are set with your default value
        of choosing.

        :param name: String. Mandatory. The name of object, does not need to be unique.
        :param location: List or tuple of length two. Mandatory. The location of the object in the grid world.
        :param customizable_properties: List. Optional, default obtained from defaults.json. The list of attribute names
        that can be customized by other objects (including AgentAvatars and as an extension any Agent).
        :param is_traversable: Boolean. Optional, default obtained from defaults.json. Signals whether other objects can
        be placed on top of this object.
        :param carried_by: List. Optional, default obtained from defaults.json. A list of who is carrying this object.
        :param visualize_size: Float. Optional, default obtained from defaults.json. A visualisation property used by
        the Visualizer. Denotes the size of the object, its unit is a single grid square in the visualisation (e.g. a
        value of 0.5 is half of a square, object is in the center, a value of 2 is twice the square's size centered on
        its location.)
        :param visualize_shape: Int. Optional, default obtained from defaults.json. A visualisation property used by the
        Visualizer. Denotes the shape of the object in the visualisation.
        :param visualize_colour: Hexcode string. Optional, default obtained from defaults.json. A visualisation property
        used by the Visualizer. Denotes the
        :param **custom_properties: Optional. Any other keyword arguments. All these are treated as custom attributes.
        For example the property 'heat'=2.4 of an EnvObject representing a fire.
        """

        # Set the object's name.
        self.obj_name = name

        # Obtain a unique ID based on a global object counter
        self.obj_id = f"{self.obj_name}_{next_obj_id()}"

        # Make customizable_properties mutable if not given
        if customizable_properties is None:
            self.customizable_properties = []

        # Set the mandatory properties to their default values based on the defaults.json if they are not given
        if is_traversable is None:
            self.is_traversable = get_default_value(class_name="EnvObject", property_name="is_traversable")
        if visualize_size is None:
            self.visualize_size = get_default_value(class_name="EnvObject", property_name="visualize_size")
        if visualize_shape is None:
            self.visualize_shape = get_default_value(class_name="EnvObject", property_name="visualize_shape")
        if visualize_colour is None:
            self.visualize_colour = get_default_value(class_name="EnvObject", property_name="visualize_colour")

        # Since carried_by cannot be defined beforehand (it contains the unique id's of objects that carry this object)
        # we set it to an empty list by default.
        if carried_by is None:
            self.carried_by = []

        # Go through the custom properties that were given (if any) and set them to the custom_properties dictionary
        self.custom_properties = {}
        for k, v in custom_properties:
            self.custom_properties[k] = v

        # Check the location
        assert isinstance(location, list)
        assert len(location) == 2

        # location should be set at the end (due to the dependency of its setter on the other properties (e.g. in
        # AgentAvatar)
        self.location = location

    def update_properties(self, grid_world):
        """
        Used to update some properties if needed. For example a 'status' property that changes over time. If you want
        this functionality, you should create a new object that inherits from this class EnvObject. Is called in
        \GridWorld after the agent actions are performed.
        :return: The new properties.
        """

        pass  # Implement this

        # Make sure that you return properties, and not simply return custom_properties as you will miss all mandatory
        # properties in that case.
        return self.properties

    def change_property(self, property_name, property_value):
        """
        Changes the value of an existing (!) property, if it can be customized (as is present in the
        customizable_properties list).
        :param property_name: The name of the property.
        :param property_value:  The value of the property.
        :return: The new properties.
        """
        # We can only change properties if they are customizable OR if this is called from the GridWorld (as the World
        # is allowed the right to change anything it wants) or the EnvObject (as the object is allowed to change itself)
        allowed_update = False
        warning_str = ""

        # We obtain the file name from which this method is called to check if it might be called from GridWorld.
        # Error sensitive when the file name of where the GridWorld class is located changes!
        caller_file = inspect.stack()[1].filename

        # If it is in customizable_properties, it is fine
        if property_name in self.customizable_properties:
            allowed_update = True
        # Then we check if the method is instead called from the GridWorld or EnvObject itself
        # See the stack method; https://docs.python.org/3.5/library/inspect.html#the-interpreter-stack)
        elif caller_file == "gridworld.py" or caller_file == "env_object.py" and allowed_update is False:
            allowed_update = True
        else:
            warning_str = f"The property name {property_name} is not a customizable property and the change is " \
                          f"called outside of the GridWorld or EnvObject class (namely from the file {caller_file})!"

        # Then we change the value of the property if we are allowed to, otherwise we give a warning and don't change
        # anything.
        if allowed_update:
            # We check if it is a custom property and if so change it simply in the dictionary
            if property_name in self.custom_properties.keys():
                self.customizable_properties[property_name] = property_value
        else:
            warnings.warn(warning_str)

        return self.properties

    def add_property(self, property_name, property_value):
        """
        Adds a new(!) property with its value to the object.
        """
        if property_name in self.custom_properties:
            raise Exception("Attribute already exists, alter value with change_property instead")
        else:
            # We always add it as a custom property which is also customizable (since we can add it)
            self.custom_properties[property_name] = property_value
            self.customizable_properties.append(property_name)

    @property
    def location(self):
        """
        The location of any object is a pythonic property, this allows us to do various checks on it. One of them is the
        setter that is overridden in AgentAvatar to also transfer all carried objects with it.
        :return: The current location as a tuple; (x, y)
        """
        return tuple(self.__location)

    @location.setter
    def location(self, loc):
        """
        The setter than can be overridden if a location change might also affect some other things inside the
        EnvObject (such as in the case of an AgentAvatar; all the objects its holding change their locations as well).
        :param loc: The new location
        """
        self.__location = loc

    @property
    def properties(self):
        """
        Returns the custom properties of this object, but also any mandatory properties such as location, name,
        is_traversable and all visualisation properties (those are in their own dictionary under 'visualisation').

        In the case we return the properties of a class that inherits from EnvObject, we check if that class has

        :return: All mandatory and custom properties in a dictionary.
        """

        # Copy the custom properties
        properties = self.custom_properties.copy()

        # Add all mandatory properties. Make sure that these are updated if one are added to the constructor!
        properties['name'] = self.obj_name
        properties['location'] = self.location
        properties['is_traversable'] = self.is_traversable
        properties['visualisation'] = {
            "size": self.visualize_size,
            "shape": self.visualize_shape,
            "colour": self.visualize_colour,
        }

        return properties

    @properties.setter
    def properties(self, property_dictionary: dict):
        """
        Here to protect the 'properties' variable. It does not do anything and should not do anything!
        """
        pass
