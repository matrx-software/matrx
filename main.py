import numpy as np

from agents.Agent import Agent, RandomAgent
from agents.capabilities.capability import SenseCapability
from environment.gridworld import GridWorld
from environment.actions.move_actions import *

seed = 1
time_step = 1  # Wait this in seconds between performing all actions
grid_size = [4, 4]  # horizontal and vertical size of grid
max_duration = 1000  # number of time units the environment should run as a maximum

strt_locations = [[0, 0], [0, 1]]
obj_locations = [[2, 2], [1, 1], [0, 3], [3, 0], [3, 3]]


grid_env = GridWorld(grid_size, max_duration, time_step, can_occupy_agent_locs=True, rnd_seed=seed)

objects = []
for nr_obj in range(len(obj_locations)):
    obj_name = f"object_{nr_obj}"
    location = obj_locations[nr_obj]
    properties = {"type": np.random.RandomState(seed).choice(["lek", "brand"]),
                  "grootte": np.random.RandomState(seed).choice([0, 1, 2])}
    is_passable = False
    grid_env.add_env_object(obj_name, location, properties, is_passable)

agents = []
for nr_agent in range(len(strt_locations)):
    agent_name = f"agent_{nr_agent}"
    poss_actions = [
        MoveNorth.__name__,
        MoveNorthEast.__name__,
        MoveEast.__name__,
        MoveSouthEast.__name__,
        MoveSouth.__name__,
        MoveSouthWest.__name__,
        MoveWest.__name__,
        MoveNorthWest.__name__]
    senses = [[None, np.inf]]
    sense_capability = SenseCapability(senses)
    agent = RandomAgent(name=agent_name, strt_location=strt_locations[nr_agent], possible_actions=poss_actions,
                        sense_capability=sense_capability)
    agents.append(agent)

    agent_id, agent_seed = grid_env.register_agent(agent_name=agent.name, location=agent.location,
                                                   sense_capability=agent.sense_capability,
                                                   get_action_func=agent.get_action,
                                                   set_action_result_func=agent.set_action_result,
                                                   agent_properties=agent.get_properties(),
                                                   action_set=agent.possible_actions)
    agent.set_rnd_seed(agent_seed)

grid_env.initialize()
is_done = False
while not is_done:
    is_done, tick_duration = grid_env.step()


print()
