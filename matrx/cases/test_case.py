import os

from matrx.agents.agent_types.human_agent import HumanAgentBrain
from matrx.agents.agent_types.patrolling_agent import PatrollingAgentBrain
from matrx.logger.log_agent_actions import LogActions
from matrx.world_builder import WorldBuilder
from matrx.actions.move_actions import *


def create_builder():
    tick_dur = 0.01
    factory = WorldBuilder(random_seed=1, shape=[15, 6], tick_duration=tick_dur, verbose=False,
                           simulation_goal=int(300/tick_dur),
                           run_matrx_api=True, run_matrx_visualizer=True, visualization_bg_clr="#000000",
                           visualization_bg_img="/static/images/soesterberg_luchtfoto.jpg")

    factory.add_logger(logger_class=LogActions, save_path="log_data/")

    even = True
    for x in range(15):
        waypoints = [(x, 0), (x, 5)]
        navigating_agent = PatrollingAgentBrain(waypoints)
        human_agent = HumanAgentBrain()
        if even:
            even = False
            start = [x, 0]
            factory.add_agent(start, navigating_agent, name="Navigate_" + str(x), visualize_shape=0, has_menu=True)
        else:
            even = True
            start = [x, 5]
            key_action_map = {
                'w': MoveNorth.__name__,
                'd': MoveEast.__name__,
                's': MoveSouth.__name__,
                'a': MoveWest.__name__
            }
            factory.add_human_agent(start, human_agent, name="human_" + str(x),
                                    key_action_map=key_action_map, visualize_shape='img',
                                    img_name="/static/images/transparent.png")

    factory.add_line(start=[1, 1], end=[3, 1], name="T")
    factory.add_line(start=[2, 2], end=[2, 4], name="T")

    factory.add_line(start=[5, 1], end=[5, 4], name="N")
    factory.add_line(start=[6, 2], end=[7, 3], name="N")
    factory.add_line(start=[8, 1], end=[8, 4], name="N")

    factory.add_line(start=[11, 1], end=[12, 1], name="O")
    factory.add_line(start=[10, 2], end=[10, 3], name="O")
    factory.add_line(start=[11, 4], end=[12, 4], name="O")
    factory.add_line(start=[13, 2], end=[13, 3], name="O")
    factory.add_object((4, 3), "Object", visualize_shape='img', img_name="/static/images/fire.gif")

    factory.add_smoke_area([0, 0], width=15, height=6, name="smoke", smoke_thickness_multiplier=0.5)
    return factory


def run_test(nr_of_worlds=1):
    builder = create_builder()

    # startup world-overarching MATRX scripts, such as the api and/or visualizer if requested
    media_folder = os.path.dirname(os.path.realpath(__file__)) # set our path for media files to our current folder
    builder.startup(media_folder=media_folder)

    # run each world
    for world in builder.worlds(nr_of_worlds=nr_of_worlds):
        world.run(builder.api_info)

    # stop MATRX scripts such as the api and visualizer (if used)
    builder.stop()
