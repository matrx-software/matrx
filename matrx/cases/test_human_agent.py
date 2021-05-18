import os

from matrx import WorldBuilder
from matrx.agents import PatrollingAgentBrain, HumanAgentBrain


def create_builder():
    tick_dur = 0.5
    builder = WorldBuilder(random_seed=1, shape=[3, 2],
                           tick_duration=tick_dur, verbose=False,
                           simulation_goal=int(300 / tick_dur),
                           run_matrx_api=True, run_matrx_visualizer=True)

    builder.add_human_agent(location=(0, 0), name="Test Human", agent=HumanAgentBrain())

    # startup world-overarching MATRX scripts, such as the api and/or
    # visualizer if requested
    media_folder = os.path.dirname(os.path.realpath(__file__))
    builder.startup(media_folder=media_folder)

    return builder


def run_test_human_agent():
    # Create builder
    builder = create_builder()

    # run each world
    world = builder.get_world()
    world.run(builder.api_info)

    # stop MATRX scripts such as the api and visualizer (if used)
    builder.stop()
