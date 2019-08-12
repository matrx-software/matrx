from matrxs.agents.human_agent_brain import HumanAgentBrain
from matrxs.agents.patrolling_agent import PatrollingAgentBrain
from matrxs.world_builder import WorldBuilder
from matrxs.actions.move_actions import *


def create_factory():
    factory = WorldBuilder(random_seed=1, shape=[15, 6], tick_duration=0.5, verbose=True,
                           run_visualization_server=True)

    even = True
    for x in range(15):
        waypoints = [(x, 0), (x, 5)]
        navigating_agent = PatrollingAgentBrain(waypoints)
        human_agent = HumanAgentBrain()
        if even:
            even = False
            start = [x, 0]
            factory.add_agent(start, navigating_agent, name="navigate " + str(x), visualize_shape=0)
        else:
            even = True
            start = [x, 5]
            usrinp_action_map = {
                'w': MoveNorth.__name__,
                'd': MoveEast.__name__,
                's': MoveSouth.__name__,
                'a': MoveWest.__name__
            }
            factory.add_human_agent(start, human_agent, name="human " + str(x),
                                    usrinp_action_map=usrinp_action_map, visualize_shape='img',
                                    img_name="transparent.png")

    factory.add_line(start=[1, 1], end=[3, 1], name="T")
    factory.add_line(start=[2, 2], end=[2, 4], name="T")

    factory.add_line(start=[5, 1], end=[5, 4], name="N")
    factory.add_line(start=[6, 2], end=[7, 3], name="N")
    factory.add_line(start=[8, 1], end=[8, 4], name="N")

    factory.add_line(start=[11, 1], end=[12, 1], name="O")
    factory.add_line(start=[10, 2], end=[10, 3], name="O")
    factory.add_line(start=[11, 4], end=[12, 4], name="O")
    factory.add_line(start=[13, 2], end=[13, 3], name="O")
    factory.add_object((4, 3), "Object", visualize_shape='img', img_name="fire.gif")
    return factory
