from matrxs.world_builder import WorldBuilder


def create_factory():
    factory = WorldBuilder(random_seed=1, shape=[14, 20], tick_duration=0.2, verbose=True, run_matrxs_api=True,
                           run_matrxs_visualizer=True, visualization_bg_clr="#f0f0f0", visualization_bg_img='/images/restaurant_bg.png')

    return factory