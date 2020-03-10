from matrxs.sim_goals.sim_goal import LimitedTimeGoal

######################
# AgentBody defaults #
######################
AGENTBODY_IS_TRAVERSABLE = False
AGENTBODY_IS_MOVABLE = False
AGENTBODY_SPEED_IN_TICKS = 1
AGENTBODY_VIS_SIZE = 1.0
AGENTBODY_VIS_COLOUR = "#92f441"
AGENTBODY_VIS_OPACITY = 1.0
AGENTBODY_VIS_SHAPE = 1
AGENTBODY_VIS_DEPTH = 100
AGENTBODY_POSSIBLE_ACTIONS = "*"

######################
# EnvObject defaults #
######################
ENVOBJECT_IS_TRAVERSABLE = False
ENVOBJECT_IS_MOVABLE = True
ENVOBJECT_VIS_SIZE = 1.0
ENVOBJECT_VIS_SHAPE = 0
ENVOBJECT_VIS_COLOUR = "#4286f4"
ENVOBJECT_VIS_OPACITY = 1.0
ENVOBJECT_VIS_DEPTH = 80

######################
# GridWorld defaults #
######################
GRIDWORLD_RANDOM_SEED = 1
GRIDWORLD_SIZE = [25, 25]
GRIDWORLD_STEP_DURATION = 0.1
GRIDWORLD_TIME_FOCUS = "step"
GRIDWORLD_RUN_VIS_SERVER = False
GRIDWORLD_RUN_API = False
GRIDWORLD_SIMULATION_GOAL = LimitedTimeGoal
GRIDWORLD_SIM_GOAL_ARGUMENTS = {
    "max_nr_ticks": -1
}
