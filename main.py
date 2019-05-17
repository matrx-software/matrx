from scenarios import test_scenario, hat_case, blanket_search_case, test_is_poss_scenario

if __name__ == "__main__":

    # By creating scripts that return a factory, we can define infinite number of use cases and select them (in the
    # future) through a UI.
    factory = test_scenario.create_factory()
    # factory = blanket_search_case.create_factory()
    # factory = hat_case.create_factory()

    world = factory.get_world()

    for world in factory.worlds():
        world.run()

    world.run()
