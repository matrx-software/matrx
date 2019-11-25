import test_scenario
from matrxs.API import api

if __name__ == "__main__":

    # By creating scripts that return a factory, we can define infinite number of use cases and select them (in the
    # future) through a UI.
    builder = test_scenario.create_factory()

    # start the API if requested
    if builder.run_matrxs_api:
        builder.run_api()

    # run each world
    for world in builder.worlds():
        world.run(builder.api_info)


    # stop the API if requested
    if builder.run_matrxs_api:
        builder.stop_api()
