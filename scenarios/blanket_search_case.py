from agents.agent import Agent
from scenario_manager.world_factory import WorldFactory, RandomProperty


def create_factory():

    factory = WorldFactory(random_seed=1, shape=[10, 10], tick_duration=0.5)

    # TODO set random properties and distributions
    random_prop = RandomProperty(values=["Geen", "Dit", "Of", "Dat"],
                                 distribution=[0.5, 0.1, 0.15, 0.25])
    factory.add_env_object(location=[0, 0], name="Wall 1", random_prop=random_prop)

    # TODO add more of those objects with the correct distributions

    agent = Agent()  # Change to BS agent
    factory.add_agent(location=[1, 0], agent=agent)

    # TODO add more agents

    return factory