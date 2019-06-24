from agents.agent import Agent
from agents.human_agent import HumanAgent
from scenario_manager.world_factory import RandomProperty, WorldFactory
from environment.actions.move_actions import *
from environment.actions.object_actions import *
from environment.objects.simple_objects import *


def create_factory():
    factory = WorldFactory(random_seed=1, shape=[10, 10], tick_duration=0.2, simulation_goal=5000, visualization_bg_clr="#6d1010")

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
    factory.add_human_agent(location=[9, 0], agent=hu_ag,
                            visualize_colour="#e9b92b", usrinp_action_map=usrinp_action_map)

    # objects to be dropped / picked up
    factory.add_env_object(location=[8, 0], name="Wall 1", is_traversable=True)
    factory.add_env_object(location=[8, 1], name="Wall 2", is_traversable=True)

    # area
    factory.add_env_object(location=[8,0], name="area1", callable_class=AreaTile, is_movable=False)

    # fog test
    # factory.add_env_object(location=[9,0], name="fog", callable_class=SmokeTile, visualize_opacity=0.8, visualize_depth=101)

    factory.add_smoke_area(top_left_location=[3,1], name="fog", width=6, height=8, avg_visualize_opacity=0.7, visualize_depth=101)

    factory.add_line(start=(4, 4), end=(6, 9), name="Line", is_movable=True)
    factory.add_room(top_left_location=(0, 0), width=3, height=3, name="room 1", door_locations=[(2, 1), (1, 2)],
                     area_visualize_colour="#af4848", doors_open=False)

    return factory
