import numpy as np

from agents.Agent import Agent
from agents.HumanAgent import HumanAgent
from agents.capabilities.capability import SenseCapability
from environment.gridworld import GridWorld
from environment.actions.move_actions import *
from environment.actions.grab_actions import *
from environment.actions.drop_actions import *
from environment.actions.object_actions import *
from environment.actions.door_actions import *
from environment.sim_goals.sim_goal import LimitedTimeGoal

seed = 1
time_step = 0.1  # Wait this in seconds between performing all actions
grid_size = [15, 15]  # horizontal and vertical size of grid
max_duration = -1  # number of time units the environment should run as a maximum

# start locations of agents = thus 2 agents
agent_start_locations = [[14, 14], [1, 1], [8, 8]]
human_agent_start_locations = [[6, 6], [9, 9]]
obj_locations = [[1, 5], [6, 0], [9, 6], [6, 3],
                 [3, 5], [7, 8], [2, 6], [8, 3]]

wall_obj_locations = [[0,0], [1,0], [2,0], [3,0], [3,1], [3,2], [3,4], [2,4], [1,4], [0,4], [0,3], [0,2], [0,1]]
block_obj_locations = [[6,0], [7,0], [8,0], [9,0], [10,0], [11,0]]
area_obj_locations = [[1,1], [2,1], [1,2], [2,2], [1,3], [2,3]]
door_obj_locations = [[3,3]]

sim_goal = LimitedTimeGoal(max_duration)  # can be a list of goals
grid_env = GridWorld(grid_size, time_step, simulation_goal=sim_goal, can_occupy_agent_locs=True, rnd_seed=seed)

objects = []
rng = np.random.RandomState(seed)
# Initialize custom objects
for nr_obj in range(len(obj_locations)):
    obj_name = f"object_{nr_obj}"
    location = obj_locations[nr_obj]
    # NOTE: np ints / floats, etc can't be JSONserialized, so convert to float!
    properties = {
                    # "type": rng.choice(["lek", "brand"]),
                  "grootte": int(rng.choice([0, 1, 2])),
                  "shape": 0,
                  "colour": rng.choice(["#286625", "#678fd9", "#FF5733"]),
                  "size": float(rng.rand()),
                  "movable": bool(rng.choice([False, True])),
                  "carried": []}

    if properties["colour"] == "#286625":
        is_traversable = False
    else:
        is_traversable = True

    grid_env.add_env_object(obj_name, location, properties, is_traversable)


# initialize walls
for nr_obj in range(len(wall_obj_locations)):
    obj_name = f"wall_object_{nr_obj}"
    location = wall_obj_locations[nr_obj]

    properties = {"type": "Wall"}

    grid_env.add_env_object(obj_name, location, properties)

# initialize blocks
for nr_obj in range(len(block_obj_locations)):
    obj_name = f"block_object_{nr_obj}"
    location = block_obj_locations[nr_obj]

    properties = {"type": "Block"}

    grid_env.add_env_object(obj_name, location, properties)

# initialize areas
for nr_obj in range(len(area_obj_locations)):
    obj_name = f"area_object_{nr_obj}"
    location = area_obj_locations[nr_obj]

    properties = {"type": "Area"}

    grid_env.add_env_object(obj_name, location, properties)

# initialize doors
for nr_obj in range(len(door_obj_locations)):
    obj_name = f"door_object_{nr_obj}"
    location = door_obj_locations[nr_obj]

    properties = {"type": "Door"}

    grid_env.add_env_object(obj_name, location, properties)




agents = []
# Initialize agents
for nr_agent in range(len(agent_start_locations)):
    agent_id = f"agent_{nr_agent}"
    poss_actions = [
        MoveNorth.__name__,
        MoveNorthEast.__name__,
        MoveEast.__name__,
        MoveSouthEast.__name__,
        MoveSouth.__name__,
        MoveSouthWest.__name__,
        MoveWest.__name__,
        MoveNorthWest.__name__,
        GrabAction.__name__,
        DropAction.__name__,
        OpenDoorAction.__name__,
        CloseDoorAction.__name__
    ]

    # specify the agent properties
    speeds = [1, 3, 6]
    agent_properties = {"size": 1, "name": f"agent_{nr_agent}", "carrying": [],
            "location": agent_start_locations[nr_agent], "is_traversable": False,
            "colour": "#900C3F", "shape": 1, "agent_speed_in_ticks": speeds[nr_agent]}
    # specify which agent properties can be changed by the agent
    properties_agent_writable = ["colour", "shape"]

    senses = [[None, np.inf]]
    sense_capability = SenseCapability(senses)
    agent = Agent(  action_set=poss_actions,
                    sense_capability=sense_capability,
                    agent_properties=agent_properties,
                    properties_agent_writable=properties_agent_writable)
    agents.append(agent)

    print(f'Created agent with speed {agent_properties["agent_speed_in_ticks"]}')


    agent_id, agent_seed = grid_env.register_agent(agent_id=agent_id,
                                                   sense_capability=agent.sense_capability,
                                                   get_action_func=agent.get_action,
                                                   set_action_result_func=agent.set_action_result,
                                                   ooda_observe=agent.ooda_observe,
                                                   ooda_orient=agent.ooda_orient,
                                                   agent_properties=agent_properties,
                                                   properties_agent_writable=properties_agent_writable,
                                                   action_set=agent.action_set,
                                                   type="agent")
    agent.set_rnd_seed(agent_seed)


human_agents = []
# Initialize human agents
for nr_human_agent in range(len(human_agent_start_locations)):
    human_agent_id = f"human_agent_{nr_human_agent}"
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

    # specify the agent properties
    hu_ag_properties = {"size": 1, "name": f"human_agent_{nr_human_agent}", "carrying": [],
            "location": human_agent_start_locations[nr_human_agent], "is_traversable": False,
            "colour": "#fde500", "shape": 1, "agent_speed_in_ticks": 1}
    # specify which agent properties can be instantly changed by the agent without cost / action
    properties_human_agent_writable = ["colour", "shape"]

    senses = [[None, np.inf]]
    sense_capability = SenseCapability(senses)
    human_agent = HumanAgent(action_set=poss_actions,
                             sense_capability=sense_capability,
                             usrinp_action_map=usrinp_action_map,
                             agent_properties=hu_ag_properties,
                             properties_agent_writable=properties_human_agent_writable)
    human_agents.append(human_agent)

    human_agent_id, human_agent_seed = grid_env.register_agent(agent_id=human_agent_id,
                                                               sense_capability=human_agent.sense_capability,
                                                               get_action_func=human_agent.get_action,
                                                               set_action_result_func=human_agent.set_action_result,
                                                               ooda_observe=human_agent.ooda_observe,
                                                               ooda_orient=human_agent.ooda_orient,
                                                               agent_properties=hu_ag_properties,
                                                               properties_agent_writable=properties_agent_writable,
                                                               action_set=human_agent.action_set,
                                                               type="humanagent")
    human_agent.set_rnd_seed(human_agent_seed)

grid_env.initialize()
is_done = False
while not is_done:
    is_done, tick_duration = grid_env.step()

print()
