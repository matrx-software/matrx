from agents.agent import Agent
from agents.human_agent import HumanAgent
from scenario_manager.world_factory import RandomProperty, WorldFactory
from environment.actions.move_actions import *
from environment.actions.object_actions import *


def create_factory():
    factory = WorldFactory(random_seed=1, shape=[10, 10], tick_duration=0.2)

    # random_prop = RandomProperty(values=["One", "Two"], distribution=[3, 1])
    # factory.add_env_object(location=[0, 0], name="Wall 1", random_prop=random_prop)

    agent = Agent()
    factory.add_agent(location=[1, 1], agent=agent, visualize_depth=5)

    # usr input action map for human agent
    usrinp_action_map = {
        'w': MoveNorth.__name__,
        'd': MoveEast.__name__,
        's': MoveSouth.__name__,
        'a': MoveWest.__name__,
        'g': GrabAction.__name__,
        'p': DropAction.__name__
    }

    hu_ag = HumanAgent()
    factory.add_human_agent(location=[6, 0], agent=hu_ag, visualize_depth=5,
                            visualize_colour="#e9b92b", usrinp_action_map=usrinp_action_map)

    factory.add_line(start=(4, 6), end=(4, 6), name="Line")

    factory.add_room(top_left_location=(0, 0), width=3, height=3, name="room 1", door_locations=[(2, 1), (1, 2)],
                     area_visualize_colour="#af4848", doors_open=False)

    return factory
