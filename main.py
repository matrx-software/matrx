from matrx.API import api
from matrx.use_cases import simple_case, test_case, new_vis_test

if __name__ == "__main__":

    # By creating scripts that return a factory, we can define infinite number of use cases and select them (in the
    # future) through a UI.
    factory = new_vis_test.create_factory()

    # startup world-overarching MATRX scripts, such as the API and/or visualizer if requested
    factory.startup()

    # run each world
    for world in factory.worlds():
        world.run(factory.api_info)

    # stop MATRX scripts such as the API and visualizer (if used)
    factory.stop()