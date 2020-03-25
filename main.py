import os
from matrx.cases import vis_test

if __name__ == "__main__":

    # By creating scripts that return a factory, we can define infinite number of use cases and select them (in the
    # future) through a UI.
    factory = vis_test.create_builder()

    # startup world-overarching MATRX scripts, such as the api and/or visualizer if requested
    media_folder = os.path.dirname(os.path.realpath(__file__)) # set our path for media files to our current folder
    factory.startup(media_folder=media_folder)

    # run each world
    for world in factory.worlds():
        world.run(factory.api_info)

    # stop MATRX scripts such as the api and visualizer (if used)
    factory.stop()