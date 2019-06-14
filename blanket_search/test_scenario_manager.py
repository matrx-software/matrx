import numpy as np
from agents.agent import Agent
from environment.scenariomanager import scenario_manager
from blanket_search.waypointnavigator import WaypointNavigator
from environment.actions.search_action import *
from environment.actions.move_actions import *
from environment.actions.object_actions import RemoveObject
from agents.capabilities.capability import SenseCapability

world = scenario_manager.scenario_manager.instantiate_scenario("environment/scenariomanager/scenario1.json")

poss_actions = [
        MoveNorth.__name__,
        MoveNorthEast.__name__,
        MoveEast.__name__,
        MoveSouthEast.__name__,
        MoveSouth.__name__,
        MoveSouthWest.__name__,
        MoveWest.__name__,
        MoveNorthWest.__name__,
        RemoveObject.__name__]
senses = [[None, np.inf]]
sense_capability = SenseCapability(senses)
agent = Agent(name="test", action_set=poss_actions,
                  sense_capability=sense_capability)
   
agent_id, agent_seed = world.register_agent(agent_name=agent.name, location=[0,0],
                                                   sense_capability=agent.sense_capability,
                                                   get_action_func=agent.get_action,
                                                   set_action_result_func=agent.set_action_result,
                                                   agent_properties=agent.get_properties(),
                                                   action_set=agent.action_set)  

print("Loaded world\n"+str(world))



plan = WaypointNavigator(agent_id)
plan.add_waypoint(1, 0, Search)
plan.add_waypoint(3, 4, Search)
print(plan)

chosen_action = plan._next_basic_action(world,poss_actions)
print (chosen_action)