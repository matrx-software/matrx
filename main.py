from blanket_search.scenarios import scenario1
from scenarios import test_scenario_huag, hat_case, test_drop_action

if __name__ == "__main__":

    # By creating scripts that return a factory, we can define infinite number of use cases and select them (in the
    # future) through a UI.
    factory = test_scenario_huag.create_factory()
    # factory = scenario1.create_factory()
    # factory = hat_case.create_factory()

    for world in factory.worlds():
        world.run()
