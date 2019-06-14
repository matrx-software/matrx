import scenario_manager.scenarios.scenario1 as scenario1
from scenario_manager.scenarios import test_scenario
from scenario_manager.scenarios import blanket_search_case

if __name__ == "__main__":

    # By creating scripts that return a factory, we can define infinite number of use cases and select them (in the
    # future) through a UI.
    factory = scenario1.create_factory(seed=3)
    # factory = scenario1.create_factory()
    # factory = blanket_search_case.create_factory()
    # factory = hat_case.create_factory()
    
    world_generator = factory.worlds(nr_of_worlds=10)
    #for world in world_generator:
    world = factory.get_world()
    world.initialize()
    world.run()

