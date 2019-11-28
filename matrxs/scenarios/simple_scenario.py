from matrxs.agents.human_agent_brain import HumanAgentBrain
from matrxs.agents.patrolling_agent import PatrollingAgentBrain
from matrxs.logger.log_agent_actions import LogActions
from matrxs.world_builder import WorldBuilder
from matrxs.actions.move_actions import *


def create_factory():
    factory = WorldBuilder(random_seed=1, shape=[15, 15], tick_duration=0.2, verbose=True, run_matrxs_api=True,
                           run_matrxs_visualizer=True)

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
