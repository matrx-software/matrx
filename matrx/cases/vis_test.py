import os

from matrx.agents import PatrollingAgentBrain, HumanAgentBrain
from matrx.world_builder import WorldBuilder
from matrx.actions import *


def create_builder():
    tick_dur = 0.1
    factory = WorldBuilder(random_seed=1, shape=[14, 20], tick_duration=tick_dur, verbose=False, run_matrx_api=True,
                           run_matrx_visualizer=True, visualization_bg_clr="#f0f0f0", simulation_goal=100000,
                           visualization_bg_img='/static/images/restaurant_bg.png')

    factory.add_room(top_left_location=[0, 0], width=14, height=20, name="world_bounds")

    n_agent = 5

    is_even = True
    is_reverse = True
    for x in range(1, n_agent + 1):
        if is_even:
            is_even = False
            if is_reverse:
                start = (x, 12)
                waypoints = [(x, 1), (x, 11)]
            else:
                start = (x, 1)
                waypoints = [(x, 11), (x, 1)]
        else:
            is_even = True
            is_reverse = False
            if is_reverse:
                start = (1, x)
                waypoints = [(11, x), (1, x)]
            else:
                start = (12, x)
                waypoints = [(1, x), (11, x)]

        navigating_agent = PatrollingAgentBrain(waypoints, move_speed=10)
        factory.add_agent(start, navigating_agent, name="navigate " + str(x), visualization_shape=2, has_menu=True,
                          is_traversable=False, visualize_when_busy=True)

    # add human agent
    key_action_map = {
        'w': MoveNorth.__name__,
        'd': MoveEast.__name__,
        's': MoveSouth.__name__,
        'a': MoveWest.__name__,
        'r': RemoveObject.__name__
    }
    factory.add_human_agent([5, 5], HumanAgentBrain(), name="human",
                            key_action_map=key_action_map, img_name="/static/images/transparent.png")

    factory.add_human_agent([6, 6], HumanAgentBrain(), name="human2",
                            key_action_map=key_action_map, img_name="/static/images/agent.gif", visualize_when_busy=True)

    # add a number of blocks to showcase the subtile functionality
    factory.add_object([6,7], "block", subtiles=[3,3], subtile_loc=[0,0], is_traversable=True, visualize_colour="#c0392b", visualize_shape=2)
    factory.add_object([6,7], "block", subtiles=[3,3], subtile_loc=[0,1], is_traversable=True, visualize_colour="#9b59b6", visualize_shape=1)
    factory.add_object([6,7], "block", subtiles=[3,3], subtile_loc=[0,2], is_traversable=True, visualize_colour="#2980b9", visualize_shape=0)
    factory.add_object([6,7], "block", subtiles=[3,3], subtile_loc=[1,0], is_traversable=True, visualize_colour="#1abc9c", visualize_shape=2, visualize_size=0.75)
    factory.add_object([6,7], "block", subtiles=[3,3], subtile_loc=[1,1], is_traversable=True, img_name="/static/images/fire.gif")
    factory.add_object([6,7], "block", subtiles=[3,3], subtile_loc=[1,2], is_traversable=True, visualize_colour="#27ae60", visualize_shape=0)
    factory.add_object([6,7], "block", subtiles=[3,3], subtile_loc=[2,0], is_traversable=True, visualize_colour="#f1c40f", visualize_shape=2, visualize_size=0.5)
    factory.add_object([6,7], "block", subtiles=[3,3], subtile_loc=[2,1], is_traversable=True, visualize_colour="#e67e22", visualize_shape=1)
    factory.add_object([6,7], "block", subtiles=[3,3], subtile_loc=[2,2], is_traversable=True, visualize_colour="#2e4053", visualize_shape=0)


    return factory


def run_vis_test(nr_of_worlds=2):
    builder = create_builder()

    # startup world-overarching MATRX scripts, such as the api and/or visualizer if requested
    media_folder = os.path.dirname(os.path.realpath(__file__)) # set our path for media files to our current folder
    builder.startup(media_folder=media_folder)

    # run each world
    for world in builder.worlds(nr_of_worlds=nr_of_worlds):
        world.run(builder.api_info)

    # stop MATRX scripts such as the api and visualizer (if used)
    builder.stop()
