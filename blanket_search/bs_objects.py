from environment.objects.env_object import EnvObject


class Brand(EnvObject):

    def __init__(self, location, omvang=None, name="Brand"):
        """
        An incident object...
        :param location: The location of the area.
        :param name: The name, default "Area".
        """
        visualization_colour ="#ff3200"
        visualization_depth =6
        visualization_size =0.3

        if omvang == "klein":
            visualization_shape =0
        elif omvang == "middelmatig":
            visualization_shape =1
        elif omvang == "groot":
            visualization_shape =2

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
        visualization_colour ="#10cec1"
        visualization_depth =5
        visualization_size =0.4

        if omvang == "klein":
            visualization_shape =1
        if omvang == "middelmatig":
            visualization_shape =2
        if omvang == "groot":
            visualization_shape =0

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
        visualization_colour ="#11ce24"
        visualization_depth =4
        visualization_size =0.5

        if omvang == "klein":
            visualization_shape =0
        if omvang == "middelmatig":
            visualization_shape =1
        if omvang == "groot":
            visualization_shape =2

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
        visualization_colour ="#1424ce"
        visualization_depth =3
        visualization_size =0.6

        if omvang == "klein":
            visualization_shape =0
        if omvang == "middelmatig":
            visualization_shape =1
        if omvang == "groot":
            visualization_shape =2

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
        visualization_colour ="#ce8013"
        visualization_depth =2
        visualization_size =0.7

        if omvang == "klein":
            visualization_shape =0
        if omvang == "middelmatig":
            visualization_shape =1
        if omvang == "groot":
            visualization_shape =2

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
        visualization_colour ="#892375"
        visualization_depth =1
        visualization_size =0.8

        if omvang == "klein":
            visualization_shape =0
        if omvang == "middelmatig":
            visualization_shape =1
        if omvang == "groot":
            visualization_shape =2

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
        visualization_colour ="#ce12be"
        visualization_depth =0
        visualization_size =0.9

        if omvang == "klein":
            visualization_shape =0
        if omvang == "middelmatig":
            visualization_shape =1
        if omvang == "groot":
            visualization_shape =2

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

        visualization_size =0.1
        visualization_shape =1

        is_traversable = True  # Areas are always traversables
        super().__init__(name=name, location=location, visualize_colour=visualization_colour,
                         visualize_size=visualization_size, visualize_shape=visualization_shape, is_traversable=is_traversable, class_callable=Waypoint)

        self.add_property("route_name", route_name)
        self.add_property("waypoint_number", waypoint_number)
