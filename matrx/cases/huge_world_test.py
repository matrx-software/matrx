from matrx.agents.agent_types.patrolling_agent import PatrollingAgentBrain
from matrx.logger.log_agent_actions import LogActions
from matrx.world_builder import WorldBuilder


def create_builder():
    size_x = 10
    size_y = 10

    factory = WorldBuilder(random_seed=1, shape=[size_x, size_y], tick_duration=0.2, run_matrx_api=True,
                           run_matrx_visualizer=True, verbose=False)

    for x in range(size_x):
        for y in range(size_y):
            factory.add_object(location=[x,y], name=f"obj_{x}_{y}")

    return factory
