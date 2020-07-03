from matrx.objects import EnvObject


class CollectBlock(EnvObject):

    def __init__(self, location, visualize_colour):
        name = "Collect block"
        super().__init__(location, name, class_callable=SignalBlock, is_traversable=True, is_movable=True,
                         visualize_shape=0, visualize_colour=visualize_colour)


class SignalBlock(EnvObject):

    def __init__(self, location, drop_zone_name, rank):
        """
        """

        self.__is_set = False
        self.__rank = rank
        self.__drop_zone_name = drop_zone_name

        name = "Signal block"
        visualize_colour = "#ffffff"
        visualize_opacity = 0.0
        # customizable_properties = ["visualize_colour", "visualize_opacity"]

        super().__init__(location, name, class_callable=SignalBlock, customizable_properties=[],
                         is_traversable=False, is_movable=False, visualize_shape=0, visualize_colour=visualize_colour,
                         visualize_opacity=visualize_opacity, rank=self.__rank, drop_zone_name=self.__drop_zone_name)

    def update(self, grid_world):
        if not self.__is_set:
            all_objs = grid_world.environment_objects
            for obj_id, obj in all_objs.items():
                if 'collection_zone_name' in obj.properties.keys() and self.__drop_zone_name == obj.properties['collection_zone_name']:
                    colour = obj.properties['collection_objects'][self.__rank]['visualization_colour']
                    self.change_property("visualization_colour", colour)
                    self.change_property("visualization_opacity", 1.0)
                    self.__is_set = True
