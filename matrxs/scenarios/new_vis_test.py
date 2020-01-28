from matrxs.world_builder import WorldBuilder


def create_factory():
    factory = WorldBuilder(random_seed=1, shape=[15, 15], tick_duration=0.2, verbose=True, run_matrxs_api=True,
                           run_matrxs_visualizer=True)

    return factory