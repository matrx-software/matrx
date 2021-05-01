import os

from matrx.objects import EnvObject
from matrx.world_builder import WorldBuilder


class KwargsObject(EnvObject):

    def __init__(self, location, name, custom_mandatory, custom_optional="optional", **kwargs):
        kwargs = {**kwargs, "custom_constructor": "constructor added"}

        super().__init__(location, name, KwargsObject, **kwargs)
        self.add_property("custom_mandatory", custom_mandatory)
        self.add_property("custom_optional", custom_optional)


class ArgsObject(EnvObject):

    def __init__(self, location, name, custom_mandatory, custom_optional="optional"):

        super().__init__(location, name, KwargsObject)
        self.add_property("custom_mandatory", custom_mandatory)
        self.add_property("custom_optional", custom_optional)


def create_builder():
    builder = WorldBuilder(random_seed=1, shape=[5, 5], tick_duration=.1, verbose=True, run_matrx_api=True,
                           run_matrx_visualizer=True, simulation_goal=-1)

    # # This should raise an exception, as the `custom_mandatory` property is not given.
    # builder.add_object(location=(2,2), name="obj_1", callable_class=ArgObject, custom_builder="builder added")

    # This should pass, as the `custom_mandatory` property is given.
    builder.add_object(location=(2, 2), name="obj_1", callable_class=KwargsObject, custom_mandatory="this is set!",
                       custom_builder="builder added")

    # This adds an object without an **kwargs element, so the custom_builder property is ignored.
    builder.add_object(location=(3, 3), name="obj_2", callable_class=ArgsObject, custom_mandatory="this is set!",
                       custom_builder="builder added")

    return builder


def run_arg_test():
    builder = create_builder()

    # startup world-overarching MATRX scripts, such as the api and/or visualizer if requested
    media_folder = os.path.dirname(os.path.realpath(__file__))  # set our path for media files to our current folder
    builder.startup(media_folder=media_folder)

    # run a world
    world = builder.get_world()
    world.run(builder.api_info)

    # stop MATRX scripts such as the api and visualizer (if used)
    builder.stop()
