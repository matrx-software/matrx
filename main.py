from scenarios import test_scenario

if __name__ == "__main__":

    # By creating scripts that return a factory, we can define infinite number of use cases and select them (in the
    # future) through a UI.
    factory = test_scenario.create_factory()

    for world in factory.worlds():
        world.run()
