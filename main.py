import numpy as np

from agents.Agent import Agent
from agents.HumanAgent import HumanAgent
from agents.capabilities.capability import SenseCapability
from environment.gridworld import GridWorld
from environment.actions.move_actions import *
from environment.sim_goals.sim_goal import LimitedTimeGoal

seed = 1
time_step = 0.1  # Wait this in seconds between performing all actions
grid_size = [10, 10]  # horizontal and vertical size of grid
max_duration = -1  # number of time units the environment should run as a maximum

# start locations of agents = thus 2 agents
agent_start_locations = [[0, 0], [0, 1]]
human_agent_start_locations = [[6, 6], [9, 9]]
obj_locations = [[2, 2], [1, 1], [0, 3], [3, 0], [3, 3]]

sim_goal = LimitedTimeGoal(max_duration)  # can be a list of goals
grid_env = GridWorld(grid_size, time_step, simulation_goal=sim_goal, can_occupy_agent_locs=True, rnd_seed=seed)

objects = []
rng = np.random.RandomState(seed)
# Initialize objects
for nr_obj in range(len(obj_locations)):
    obj_name = f"object_{nr_obj}"
    location = obj_locations[nr_obj]
    # NOTE: np ints / floats, etc can't be JSONserialized, so convert to float!
    properties = {"type": rng.choice(["lek", "brand"]),
                  "grootte": int(rng.choice([0, 1, 2])),
                  "shape": 0,
                  "colour": rng.choice(["#286625", "#678fd9", "#FF5733"]),
                  "size": float(rng.rand())}
    is_traversable = False
    grid_env.add_env_object(obj_name, location, properties, is_traversable)

agents = []
# Initialize agents
for nr_agent in range(len(agent_start_locations)):
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
    agent = Agent(name=agent_name, action_set=poss_actions,
                  sense_capability=sense_capability, grid_size=grid_env.shape)
    agents.append(agent)

    agent_id, agent_seed = grid_env.register_agent(agent_name=agent.name, location=agent_start_locations[nr_agent],
                                                   sense_capability=agent.sense_capability,
                                                   get_action_func=agent.get_action,
                                                   set_action_result_func=agent.set_action_result,
                                                   agent_properties=agent.get_properties(),
                                                   action_set=agent.action_set)
    agent.set_rnd_seed(agent_seed)

human_agents = []
# Initialize human agents
for nr_human_agent in range(len(human_agent_start_locations)):
    human_agent_name = f"human_agent_{nr_human_agent}"
    poss_actions = [
        MoveNorth.__name__,
        MoveEast.__name__,
        MoveSouth.__name__,
        MoveWest.__name__
    ]
    usrinp_action_map = {
        'arrowkey:up': MoveNorth.__name__,
        'arrowkey:right': MoveEast.__name__,
        'arrowkey:down': MoveSouth.__name__,
        'arrowkey:left': MoveWest.__name__
    }
    senses = [[None, np.inf]]
    sense_capability = SenseCapability(senses)
    human_agent = HumanAgent(name=human_agent_name, action_set=poss_actions,
                             sense_capability=sense_capability, grid_size=grid_env.shape,
                             usrinp_action_map=usrinp_action_map)
    human_agents.append(human_agent)

    human_agent_id, human_agent_seed = grid_env.register_agent(agent_name=human_agent.name,
                                                               location=human_agent_start_locations[nr_human_agent],
                                                               sense_capability=human_agent.sense_capability,
                                                               get_action_func=human_agent.get_action,
                                                               set_action_result_func=human_agent.set_action_result,
                                                               agent_properties=human_agent.get_properties(),
                                                               action_set=human_agent.action_set)
    human_agent.set_rnd_seed(human_agent_seed)

grid_env.initialize()
is_done = False
while not is_done:
    is_done, tick_duration = grid_env.step()

print()
