import os

from matrx.agents.agent_types.patrolling_agent import PatrollingAgentBrain
from matrx.logger.log_agent_actions import LogActions
from matrx.world_builder import WorldBuilder


def create_builder():
    tick_dur = 0.2
    factory = WorldBuilder(random_seed=1, shape=[15, 15], tick_duration=tick_dur, verbose=True, run_matrx_api=True,
                           run_matrx_visualizer=True, simulation_goal=int(300/tick_dur))

    factory.add_logger(logger_class=LogActions, save_path="log_data/")

    factory.add_room(top_left_location=[0, 0], width=15, height=15, name="world_bounds")

    n_agent = 1

    is_even = True
    is_reverse = True
    for x in range(1, n_agent+1):
        if is_even:
            is_even = False
            if is_reverse:
                start = (x, 14)
                waypoints = [(x, 1), (x, 13)]
            else:
                start = (x, 1)
                waypoints = [(x, 13), (x, 1)]
        else:
            is_even = True
            is_reverse = False
            if is_reverse:
                start = (1, x)
                waypoints = [(13, x), (1, x)]
            else:
                start = (14, x)
                waypoints = [(1, x), (13, x)]

        navigating_agent = PatrollingAgentBrain(waypoints, move_speed=10)
        factory.add_agent(start, navigating_agent, name="navigate " + str(x), visualize_shape=0, has_menu=True)

    return factory


def run_simple_case(nr_of_worlds=1):
    builder = create_builder()

    # startup world-overarching MATRX scripts, such as the api and/or visualizer if requested
    media_folder = os.path.dirname(os.path.realpath(__file__))  # set our path for media files to our current folder
    builder.startup(media_folder=media_folder)

    # run each world
    for world in builder.worlds(nr_of_worlds=nr_of_worlds):
        world.run(builder.api_info)

    # stop MATRX scripts such as the api and visualizer (if used)
    builder.stop()
