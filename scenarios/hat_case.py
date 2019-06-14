from agents.agent import Agent
from scenario_manager.world_factory import RandomProperty, WorldFactory


def create_factory():
    factory = WorldFactory(random_seed=1, shape=[50, 50], tick_duration=0.5)

    # TODO Build the 'compound protection case'

    return factory