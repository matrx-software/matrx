from agents.Agent import Agent
from agents.HumanAgent import HumanAgent
from scenario_manager.world_factory import RandomProperty, WorldFactory


def create_factory():
    factory = WorldFactory(random_seed=1, shape=[10, 10], tick_duration=0.5)


    # Obj for testing visualization depth, this block should be in front
    factory.add_env_object(location=[3,3], is_movable=False, is_traversable=True, visualize_shape=0, visualize_colour="#000000", name="overlaying_block", visualize_depth=3)

    # Obj for testing visualization depth, this block should be in front
    factory.add_env_object(location=[3,3], is_movable=False, is_traversable=True, visualize_shape=0, visualize_colour="#000000", name="bottom_block", visualize_depth=1)

    # Obj for testing visualization depth, this block should be in front
    factory.add_env_object(location=[3,3], is_movable=False, is_traversable=True, visualize_shape=0, visualize_colour="#000000", name="top_block", visualize_depth=4)


    return factory
