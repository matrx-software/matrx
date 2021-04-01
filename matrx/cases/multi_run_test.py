from tqdm import tqdm
import matrx
from matrx import WorldBuilder
from matrx.agents import AgentBrain
from matrx.actions import MoveNorth
from matrx.actions.object_actions import DropObject

class IdleAgent(AgentBrain):
    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def filter_observations(self, state):
        return state

    def decide_on_action(self, state):
        return MoveNorth.__name__, {'action_duration': 0}


def test_builder(run_matrx_api, run_matrx_visualizer, tick_speed):
    builder = WorldBuilder(shape=[9, 10], run_matrx_api=run_matrx_api, run_matrx_visualizer=run_matrx_visualizer,
                           visualization_bg_img='', tick_duration=tick_speed,
                          simulation_goal = 500)
    builder.add_room(top_left_location=[0, 0], width=9, height=10, name='Wall_Border')

    brain = IdleAgent()
    builder.add_agent([3, 1], brain, name='agent')


    return builder

def run_sim():
    builder = test_builder(run_matrx_api=False, run_matrx_visualizer=False, tick_speed=0)
    builder.startup()
    world = builder.get_world()
    world.run(api_info=builder.api_info)
    builder.stop()

for i in tqdm(range(1000)):
    run_sim()