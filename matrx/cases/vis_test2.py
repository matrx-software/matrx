import os

from matrx.agents import PatrollingAgentBrain, HumanAgentBrain
from matrx.logger.log_messages import MessageLogger
from matrx.world_builder import WorldBuilder
from matrx.actions import *
from datetime import datetime
from matrx.objects import Door, SquareBlock, AreaTile, SmokeTile, CollectionDropOffTile
from matrx.agents import HumanAgentBrain

def create_builder2():
    tick_dur = 0.1
    factory = WorldBuilder(random_seed=1, shape=[9, 10], tick_duration=1, verbose=False, run_matrx_api=True,
                           run_matrx_visualizer=True, visualization_bg_clr="#f0f0f0", simulation_goal=100000)

    factory.add_room(top_left_location=[0, 0], width=9, height=10, name='Wall_Border', wall_visualize_opacity=0.5)
    factory.add_object(location=[3,3], name="door", callable_class=Door, visualize_opacity=0.5, is_open=False)
    factory.add_object(location=[3,4], name="block", callable_class=SquareBlock, visualize_opacity=0.5)
    factory.add_object(location=[3,5], name="tile1", callable_class=AreaTile, visualize_opacity=0.5)
    factory.add_object(location=[3,6], name="tile2", callable_class=SmokeTile, visualize_opacity=0.5)
    factory.add_object(location=[4,6], name="CollectionDropOffTile", callable_class=CollectionDropOffTile, visualize_opacity=0.5)

    factory.add_human_agent(location=[5,6], agent=HumanAgentBrain(), visualize_opacity=0.5)

    return factory


def run_vis_test2(nr_of_worlds=2):
    builder = create_builder2()

    # startup world-overarching MATRX scripts, such as the api and/or visualizer if requested
    media_folder = os.path.dirname(os.path.realpath(__file__)) # set our path for media files to our current folder
    builder.startup(media_folder=media_folder)

    # run each world
    for world in builder.worlds(nr_of_worlds=nr_of_worlds):
        # builder.api_info['matrx_paused'] = False
        world.run(builder.api_info)

    # stop MATRX scripts such as the api and visualizer (if used)
    builder.stop()
