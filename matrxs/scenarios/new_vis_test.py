from matrxs.agents.patrolling_agent import PatrollingAgentBrain
from matrxs.world_builder import WorldBuilder


def create_factory():
    factory = WorldBuilder(random_seed=1, shape=[14, 20], tick_duration=0.2, verbose=True, run_matrxs_api=True,
                           run_matrxs_visualizer=True, visualization_bg_clr="#f0f0f0", visualization_bg_img='/images/restaurant_bg.png')

    # factory.add_room(top_left_location=[0, 0], width=14, height=20, name="world_bounds")
    #
    # n_agent = 1
    #
    # is_even = True
    # is_reverse = True
    # for x in range(1, n_agent + 1):
    #     if is_even:
    #         is_even = False
    #         if is_reverse:
    #             start = (x, 14)
    #             waypoints = [(x, 1), (x, 13)]
    #         else:
    #             start = (x, 1)
    #             waypoints = [(x, 13), (x, 1)]
    #     else:
    #         is_even = True
    #         is_reverse = False
    #         if is_reverse:
    #             start = (1, x)
    #             waypoints = [(13, x), (1, x)]
    #         else:
    #             start = (14, x)
    #             waypoints = [(1, x), (13, x)]
    #
    #     navigating_agent = PatrollingAgentBrain(waypoints, move_speed=10)
    #     factory.add_agent(start, navigating_agent, name="navigate " + str(x), visualize_shape=0, has_menu=True)

    return factory