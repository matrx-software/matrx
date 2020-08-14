import os

from matrx import WorldBuilder
from matrx.agents import PatrollingAgentBrain


def create_builder():
    tick_dur = 0.5
    builder = WorldBuilder(random_seed=1, shape=[3, 2],
                           tick_duration=tick_dur, verbose=False,
                           simulation_goal=int(300 / tick_dur),
                           run_matrx_api=True, run_matrx_visualizer=True)

    start = (0, 0)
    waypoints = [(0, 0), (0, 1)]
    agent = PatrollingAgentBrain(waypoints)
    builder.add_agent(start, agent, name="Navigate", visualize_shape=0,
                      has_menu=True, is_traversable=False)


    start = (0, 1)
    waypoints = [(0, 1)]
    agent = PatrollingAgentBrain(waypoints)
    builder.add_agent(start, agent, name="Navigate 2", visualize_shape=1,
                      has_menu=True, is_traversable=False)

    # startup world-overarching MATRX scripts, such as the api and/or
    # visualizer if requested
    media_folder = os.path.dirname(os.path.realpath(__file__))
    builder.startup(media_folder=media_folder)

    return builder


def run_test_navigators():
    # Create builder
    builder = create_builder()

    # run each world
    world = builder.get_world()
    world.run(builder.api_info)

    # stop MATRX scripts such as the api and visualizer (if used)
    builder.stop()
