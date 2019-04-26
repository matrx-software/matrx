import json
import os
from pathlib import Path
from warnings import warn


class ScenarioManager:

    def __init__(self):
        self.scenario_file = None
        self.scenario_dict = None
        self.defaults = self._load_defaults()

    def create_scenario(self, scenario_file):

        # Get the full path to the scenario file
        self.scenario_dict = self._load_scenario_json(scenario_path)

        # TODO : check if agent names (grouped by their class) are unique, if not append a unique number and use as id
        agents = self._create_agents()

        areas = self._create_areas()

        objects = self._create_objects()

        return None

    def _create_agents(self):
        # If there was no agent
        if "agents" not in self.scenario_dict.keys():
            warn(f"You are creating a scenario from {self.scenario_file} that does not contain an 'agents' section.")
            return []

        agent_settings = self.scenario_dict['agents']

    def _create_areas(self):
        pass

    def _create_objects(self):
        pass

    def _load_defaults(self):
        root_path = Path(__file__).parents[1]
        file_path = os.path.join(root_path, "scenarios", "defaults.json")
        return self._load_json(file_path)

    def _load_scenario(self, scenario_file):
        self.scenario_file = scenario_file
        root_path = Path(__file__).parents[1]
        scenario_path = os.path.join(root_path, "scenarios", scenario_file)
        return self._load_json(scenario_path)

    def _load_json(self, file_path):
        with open(file_path, "r") as read_file:
            scenario_dict = json.load(read_file)
        return scenario_dict

