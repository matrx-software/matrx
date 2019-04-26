from scenario_manager.manager import ScenarioManager

if __name__ == "__main__":

    scenario_file = "test.json"

    # Create the scenario's grid world
    grid_world = ScenarioManager().create_scenario(scenario_file=scenario_file)

    # Run the grid world
    grid_world.run()