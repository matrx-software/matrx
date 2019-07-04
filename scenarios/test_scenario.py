from agents.agent import Agent
from world_factory.world_factory import RandomProperty, WorldFactory


def create_factory():
    factory = WorldFactory(random_seed=1, shape=[10, 10], tick_duration=0.5)

    random_prop = RandomProperty(values=["One", "Two"], distribution=[3, 1])
    factory.add_env_object(location=[0, 0], name="Wall 1", random_prop=random_prop)

    # Obj for testing visualization depth, this block should be in front
    factory.add_env_object(location=[3, 3], is_movable=False, is_traversable=True, visualize_shape=0,
                           visualize_colour="#000000", name="overlaying_block", visualize_depth=3)

    agent = Agent()
    factory.add_agent(location=[1, 0], agent=agent, visualize_depth=5)

    agents = [Agent() for _ in range(3)]
    locs = [[1, 1], [2, 2], [3, 3]]
    factory.add_multiple_agents(agents=agents, locations=locs)

    # hu_agent = HumanAgent()
    # factory.add_human_agent(location=[4,1], agent=hu_agent)

    factory.add_multiple_objects([[4, 4], [5, 5], [6, 6]])

    return factory
