from agents.agent_brain import AgentBrain
from agents.navigating_agent_test import NavigatingAgentBrain
from world_factory.world_factory import RandomProperty, WorldFactory


def create_factory():
    factory = WorldFactory(random_seed=1, shape=[10, 10], tick_duration=0.5, verbose=True)

    waypoints = [(0, 9), (9, 9), (9, 0), (0, 0)]
    navigating_agent = NavigatingAgentBrain(waypoints)
    factory.add_agent([0, 0], navigating_agent)

    # waypoints = [(1, 8), (8, 8), (8, 1), (1, 1)]
    # navigating_agent = NavigatingAgentBrain(waypoints)
    # factory.add_agent([1, 1], navigating_agent)

    # waypoints = [(2, 7), (7, 7), (7, 2), (2, 2)]
    # navigating_agent = NavigatingAgentBrain(waypoints)
    # factory.add_agent([2, 2], navigating_agent)

    # factory.add_env_object(location=[0, 5], name="Wall 1")

    # random_prop = RandomProperty(values=["One", "Two"], distribution=[3, 1])
    # factory.add_env_object(location=[0, 0], name="Wall 1", random_prop=random_prop)

    # Obj for testing visualization depth, this block should be in front
    # factory.add_env_object(location=[3, 3], is_movable=False, is_traversable=True, visualize_shape=0,
    #                       visualize_colour="#000000", name="overlaying_block", visualize_depth=3)

    # agent = AgentBrain()
    # sense_capability = factory.create_sense_capability(["*"], [3])
    # factory.add_agent(location=[1, 0], agent=agent, visualize_depth=5, sense_capability=sense_capability)

    # agent = AgentBrain()
    # sense_capability = factory.create_sense_capability(["*"], [3])
    # factory.add_agent(location=[1, 1], agent=agent, visualize_depth=5, sense_capability=sense_capability)

    # agents = [AgentBrain() for _ in range(3)]
    # locs = [[1, 1], [2, 2], [3, 3]]
    # factory.add_multiple_agents(agents=agents, locations=locs, sense_capabilities=sense_capability)

    # hu_agent = HumanAgent()
    # factory.add_human_agent(location=[4,1], agent=hu_agent)

    # factory.add_multiple_objects([[4, 4], [5, 5], [6, 6]])

    return factory
