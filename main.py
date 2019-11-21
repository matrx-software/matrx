import test_scenario

if __name__ == "__main__":

    # By creating scripts that return a factory, we can define infinite number of use cases and select them (in the
    # future) through a UI.
    builder = test_scenario.create_factory()
    builder.run_api()

    for world in builder.worlds():
        world.run()

    builder.stop_api()
