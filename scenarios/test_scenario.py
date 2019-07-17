from agents.agent_brain import AgentBrain
from agents.human_agent_brain import HumanAgentBrain
from agents.navigating_agent_test import NavigatingAgentBrain
from world_factory.world_factory import RandomProperty, WorldFactory


def create_factory():
    factory = WorldFactory(random_seed=1, shape=[15, 6], tick_duration=0.5, visualization_bg_img="soesterberg_luchtfoto.jpg", verbose=True)

    even = True
    for x in range(15):
        waypoints = [(x, 0), (x, 5)]
        navigating_agent = NavigatingAgentBrain(waypoints)
        human_agent = HumanAgentBrain()
        if even:
            even = False
            start = [x, 0]
            factory.add_agent(start, navigating_agent, name="navigate " + str(x), visualize_shape=2)
        else:
            even = True
            start = [x, 5]
            factory.add_human_agent(start, human_agent, name="human " + str(x), visualize_shape='img', imgName="transparent.png")

    factory.add_line(start=[1, 1], end=[3, 1], name="T")
    factory.add_line(start=[2, 2], end=[2, 4], name="T")

    factory.add_line(start=[5, 1], end=[5, 4], name="N")
    factory.add_line(start=[6, 2], end=[7, 3], name="N")
    factory.add_line(start=[8, 1], end=[8, 4], name="N")

    factory.add_line(start=[11, 1], end=[12, 1], name="O")
    factory.add_line(start=[10, 2], end=[10, 3], name="O")
    factory.add_line(start=[11, 4], end=[12, 4], name="O")
    factory.add_line(start=[13, 2], end=[13, 3], name="O")

    return factory
