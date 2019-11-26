from matrxs.API import api
from matrxs.scenarios import simple_scenario

if __name__ == "__main__":

    # By creating scripts that return a factory, we can define infinite number of use cases and select them (in the
    # future) through a UI.
    factory = simple_scenario.create_factory()

    # start the API if requested
    if factory.run_matrxs_api:
        factory.run_api()

    # run each world
    for world in factory.worlds():
        world.run(factory.api_info)


    # stop the API if requested
    if factory.run_matrxs_api:
        factory.stop_api()
