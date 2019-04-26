import json
import os
from pathlib import Path
from warnings import warn
import numpy as np

from agents.HumanAgent import HumanAgent
from agents.capabilities.capability import SenseCapability
from environment.gridworld import GridWorld
from environment.objects.basic_objects import EnvObject
from environment.sim_goals.sim_goal import SimulationGoal


class ScenarioManager:

    def __init__(self):
        self.scenario_file = None
        self.scenario_dict = None
        self.defaults = self._load_defaults_json()

    def create_scenario(self, scenario_file):

        # Get the full path to the scenario file
        self.scenario_dict = self._load_scenario_json(scenario_file)

        # Get simulation settings
        grid_world = self._create_grid_world()

        # TODO : check if agent names (grouped by their class) are unique, if not append a unique number and use as id
        agents = self._create_agents(grid_world)

        areas = self._create_areas(grid_world)

        objects = self._create_objects(grid_world)

        return None

    def _create_grid_world(self):
        # If there is no simulation settings section, we warn the user
        if "simulation_settings" not in self.scenario_dict.keys():
            warn(f"You are creating a scenario from {self.scenario_file} that does not contain an 'simulation_settings'"
                 f" section. The scenario will run with all default simulation settings.")
            settings = self.defaults["simulation_settings"]
        else:
            settings = self.scenario_dict["simulation_settings"]
            settings = self._add_missing_keys(settings, self.defaults["simulation_defaults"])

        goal_class = settings["simulation_goal"]["goal_class"]
        goal_arguments = settings["simulation_goal"]["arguments"]
        sim_goal = self._runtime_object_creation(goal_class, goal_arguments, SimulationGoal)
        grid_world = GridWorld(shape=settings['size'],
                               tick_duration=settings['step_duration'],
                               simulation_goal=sim_goal,
                               rnd_seed=settings['random_seed'],
                               run_sail_api=settings['run_sail_api'],
                               run_visualisation_server=settings['run_visualisation_server'],
                               time_focus=settings['time_focus'])

        return grid_world

    def _create_agents(self, grid_world: GridWorld):
        # If there is no agent section, we warn the user
        if "agents" not in self.scenario_dict.keys():
            warn(f"You are creating a scenario from {self.scenario_file} that does not contain an 'agents' section.")
            return []

        # Obtain the agents section
        agent_settings = self.scenario_dict['agents']

        # We separate the agents in HumanAgents and not HumanAgents (as they are treated slightly different with
        # different basic defaults.)
        agents = {}  # dict for agents; name/id : agent_settings
        human_agents = {}  # dict for human_agents; name/id : human_agent_settings
        # counters used to make unique names (later used as id's as well) if names are duplicates
        agent_id_nr = 0
        human_agent_id_nr = 0
        for agent_setting in agent_settings:  # loop through settings
            if "agent_class" in agent_setting and agent_setting["agent_class"] == HumanAgent.__name__:  # if human agent
                default_settings = self.defaults["human_agent_defaults"]
                settings = self._add_missing_keys(agent_setting, default_settings)  # add default settings if missing
                name = settings['name']
                if name in human_agents.keys():  # if name already exists, make unique with simple integer counter
                    name = f"{name}_{human_agent_id_nr}"
                    human_agent_id_nr += 1
                human_agents[name] = settings
            else:  # if Agent (or some inheritance of it)
                default_settings = self.defaults["agent_defaults"]
                settings = self._add_missing_keys(agent_setting, default_settings)
                name = settings['name']
                if name in agents.keys():  # if duplicate names, we use the agent counter
                    name = f"{name}_{agent_id_nr}"
                    agent_id_nr += 1
                agents[name] = settings

        # Create all HumanAgents
        for agent_id, settings in human_agents.items():
            self._create_human_agent(agent_id, settings, grid_world)

        # Create all Agents
        for agent_id, settings in agents.items():
            pass


    def _create_areas(self, grid_world: GridWorld):
        pass

    def _create_objects(self, grid_world: GridWorld):
        pass

    def _load_defaults_json(self):
        root_path = Path(__file__).parents[1]
        file_path = os.path.join(root_path, "scenarios", "defaults.json")
        return self._load_json(file_path)

    def _load_scenario_json(self, scenario_file):
        self.scenario_file = scenario_file
        root_path = Path(__file__).parents[1]
        scenario_path = os.path.join(root_path, "scenarios", scenario_file)
        return self._load_json(scenario_path)

    def _load_json(self, file_path):
        with open(file_path, "r") as read_file:
            scenario_dict = json.load(read_file)
        return scenario_dict

    def _add_missing_keys(self, settings: dict, defaults: dict):
        for k, v in defaults.items():
            if k not in settings.keys():
                settings[k] = v
            else:
                if isinstance(v, dict):
                    v = self._add_missing_keys(settings[k], v)
                    settings[k] = v

        return settings

    def _runtime_object_creation(self, class_name, kwargs, super_type):

        # Search for all subclasses of super_type first in the entire code base
        classes_dict = self._get_all_inherited_classes(super_type)

        # If the class is known, we call its constructor with the kwargs
        if class_name in classes_dict.keys():
            return classes_dict[class_name](**kwargs)
        else:
            return None

    def _get_sense_capability(self, senses):
        # Get all potential EnvObject classes
        potential_objects = self._get_all_inherited_classes(EnvObject)

        trans_senses = []
        for sense in senses:
            sense_class = sense[0]
            sense_range = sense[1]

            if isinstance(sense_range, str):
                sense_range = np.inf
            if sense_class == "*":
                sense_class = None

            if sense_class in potential_objects.items():
                trans_senses.append([sense_class, sense_range])

        return SenseCapability(trans_senses)

    def _get_all_inherited_classes(self, super_type):
        all_classes = {super_type}
        work = [super_type]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in all_classes:
                    all_classes.add(child)
                    work.append(child)

        # Create a dict out of it
        class_dict = {}
        for classes in all_classes:
            class_dict[classes.__name__] = classes

        return class_dict

    def _create_human_agent(self, agent_id, settings, grid_world):
        # Check if settings contains the one mandatory setting that is not in defaults; start_location
        if "start_location" not in settings.keys():
            raise Exception(f"Cannot add the agent {agent_id}; the 'location' is missing in the scenario json "
                            f"file.")

        # make sure that all key input actions are in 'all_actions'
        all_actions = settings['possible_actions']
        all_actions.extend(settings["input_action_map"].keys())
        all_actions = set(all_actions)

        # Create the sense capability
        sense_capability = self._get_sense_capability(settings["senses"])

        # Get use inputs map
        user_inputs_map = settings["input_action_map"]

        # Get agent properties, and add our mandatory properties to it as well (e.g., location, size, colour, etc.)
        agent_properties = settings["additional_agent_properties"]
        agent_properties["location"] = settings["start_location"]
        agent_properties["size"] = settings["visualisation_properties"]["size"]
        agent_properties["colour"] = settings["visualisation_properties"]["colour"]
        agent_properties["shape"] = settings["visualisation_properties"]["shape"]
        agent_properties["is_traversable"] = settings["is_traversable"]
        agent_properties["agent_speed_in_ticks"] = settings["agent_speed_in_ticks"]
        agent_properties["name"] = agent_id

        properties_agent_writable = settings["agent_properties_writable"]
        human_agent = HumanAgent(action_set=all_actions, sense_capability=sense_capability,
                                 usrinp_action_map=user_inputs_map, agent_properties=agent_properties,
                                 properties_agent_writable=properties_agent_writable)

        # Register the agent to the grid world
        _, seed = grid_world.register_agent(agent_id=agent_id,
                                            sense_capability=human_agent.sense_capability,
                                            get_action_func=human_agent.get_action,
                                            set_action_result_func=human_agent.set_action_result,
                                            ooda_observe=human_agent.ooda_observe,
                                            ooda_orient=human_agent.ooda_orient,
                                            agent_properties=agent_properties,
                                            properties_agent_writable=properties_agent_writable,
                                            action_set=human_agent.action_set,
                                            class_name_agent=settings["agent_class"])

        # Set the random seed we obtained from the grid world for this agent
        human_agent.set_rnd_seed(seed=seed)
