import json
import os
from pathlib import Path
from typing import Callable, Mapping
from warnings import warn
import numpy as np
from shapely.geometry import Polygon, Point

from agents.Agent import Agent
from agents.HumanAgent import HumanAgent
from agents.capabilities.capability import SenseCapability
from environment.actions.action import Action
from environment.gridworld import GridWorld
from environment.objects.basic_objects import EnvObject, Area, Wall, Door
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

        agents = self._create_agents(grid_world)

        areas = self._create_areas(grid_world)

        objects = self._create_objects(grid_world)

        return None

    def _fill_grid_world(self, grid_world, agents, areas, objects):
        # Create all Agents
        for agent_id_name, settings in agents.items():
            self._create_agent(agent_id_name, settings, grid_world)

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
        for agent_id_name, settings in human_agents.items():
            self._create_human_agent(agent_id_name, settings, grid_world)

        return agents

    def _create_areas(self, grid_world: GridWorld):
        # Obtain the areas section
        areas_settings = self.scenario_dict['areas']

        areas = []
        for area_settings in areas_settings:
            area = self._get_area(area_settings)
            areas.append(area)

        return areas

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

        # Go through the list of (Type, range) tuples
        trans_senses = []
        for sense in senses:
            sense_class = sense[0]  # class type
            sense_range = sense[1]  # range

            if isinstance(sense_range, str):  # if range is a string (e.g. "*") its infinite
                sense_range = np.inf
            if sense_class == "*":  # if the wildcard "*" is used, we set sense_class to None, denoting all classes
                sense_class = None

            if sense_class in potential_objects.items():  # append the processed tuple to the new list of senses
                trans_senses.append([sense_class, sense_range])

        return SenseCapability(trans_senses)  # return a SenseCapability based on the processed senses list

    def _get_all_inherited_classes(self, super_type) -> Mapping[str, Callable]:
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

    def _create_agent(self, agent_id, settings, grid_world):
        # Check if settings contains the one mandatory setting that is not in defaults; start_location
        if "start_location" not in settings.keys():
            raise Exception(f"Cannot add the agent {agent_id}; the 'location' is missing in the scenario json "
                            f"file.")

        # Process and get the actions
        all_actions = self._get_action_list(agent_id, settings['possible_actions'])

        # Get the agent's brain class (defaults to Agent, a random behavior agent)
        class_name = settings['agent_class']
        agent_class = self._get_class(class_name, Agent, id_name=agent_id)

        # Ge the agents properties, and add our mandatory properties to it as well (e.g., location, size, colour, etc.)
        agent_properties = settings["additional_agent_properties"]
        agent_properties["location"] = settings["start_location"]
        agent_properties["size"] = settings["visualisation_properties"]["size"]
        agent_properties["colour"] = settings["visualisation_properties"]["colour"]
        agent_properties["shape"] = settings["visualisation_properties"]["shape"]
        agent_properties["is_traversable"] = settings["is_traversable"]
        agent_properties["agent_speed_in_ticks"] = settings["agent_speed_in_ticks"]
        agent_properties["name"] = agent_id

        # Get the properties the agent's brain can write to
        properties_agent_writable = settings['agent_properties_writable']

        # Create the sense capability
        sense_capability = self._get_sense_capability(settings["senses"])

        # Get the agent's kwargs
        kwargs = settings['class_specific_kwargs']

        # Create the agent's brain based on the appropriate class
        agent = agent_class(action_set=all_actions,
                            sense_capability=sense_capability,
                            agent_properties=agent_properties,
                            properties_agent_writable=properties_agent_writable,
                            **kwargs)

        # Register the agent to the grid world, returns us the agent_id with which it is known and a generated rnd seed
        agent_id, agent_seed = grid_world.register_agent(agent_id=agent_id,
                                                         sense_capability=agent.sense_capability,
                                                         get_action_func=agent.get_action,
                                                         set_action_result_func=agent.set_action_result,
                                                         ooda_observe=agent.ooda_observe,
                                                         ooda_orient=agent.ooda_orient,
                                                         agent_properties=agent_properties,
                                                         properties_agent_writable=properties_agent_writable,
                                                         action_set=agent.action_set,
                                                         class_name_agent=agent_class)

        # Set the random seed for this agent's brain with a seed generated from the master rng in grid world
        agent.set_rnd_seed(agent_seed)

    def _get_action_list(self, agent_id, action_list):
        # Get list of all Action class types known in the project
        all_actions = self._get_all_inherited_classes(Action).keys()

        # Go through all actions, throw exception when there is one unknown in the project or if there is a wildcard '*'
        # present, we return all known actions.
        for action_name in action_list:
            if action_name == "*":  # wildcard denoting all actions:
                return list(all_actions)
            else:  # if not a wildcard we parse the action class name (throws exception if class is not known)
                self._get_class(action_name, Action, id_name=agent_id)

        # If we got through the exception check, we return the original list
        return action_list

    def _get_class(self, class_name, super_class, id_name=None):
        # Get all possible agent brain classes and check if the 'agent_class' is among them
        all_classes = self._get_all_inherited_classes(super_class)
        if class_name not in all_classes.keys():  # if class name is not known
            if id_name is not None:
                raise Exception(f"Cannot add {id_name}; the class '{class_name}' is not among the classes"
                                f"that inherit from Agent and therefore cannot be defined.")
            else:
                raise Exception(f"Cannot add object; the agent class '{class_name}' is not among the classes"
                                f"that inherit from {super_class} and therefore cannot be defined.")
        else:  # class name is known
            callable_class = all_classes[class_name]

        return callable_class

    def _get_area(self, area_settings):
        # Append missing settings (if any)
        default_settings = self.defaults["area_defaults"]
        settings = self._add_missing_keys(area_settings, default_settings)  # add default settings if missing

        # Boolean whether we should add wall objects on the edges
        generate_walls = settings['has_walls']

        # Get the corner coordinates (in order in wwhich we should connect them)
        ordered_corners = settings['corners']

        # Get the door coordinates
        doors = settings['doors']

        # Get the volume coordinates and all coordinates on the convex hull formed by the polygon based on the corners
        hull_coords, volume_coords = self._get_hull_and_volume_coords(ordered_corners)

        # Get area, wall and door objects
        area_obj, wall_obj, door_obj = self._get_area_tiles(volume_coords, hull_coords, doors, generate_walls,
                                                            settings)

        # Area object consist out of a tuple; area_objects, wall_objects, door_objects
        return (area_obj, wall_obj, door_obj)

    def _get_hull_and_volume_coords(self, corner_coords):
        # Get the polygon represented by the corner coordinates
        # TODO remove the dependency to Shapely
        polygon = Polygon(corner_coords)

        (minx, miny, maxx, maxy) = polygon.bounds
        minx = int(minx)
        miny = int(miny)
        maxx = int(maxx)
        maxy = int(maxy)
        print("poly.bounds:", polygon.bounds)
        volume_coords = []
        for x in range(minx, maxx + 1):
            for y in range(miny, maxy + 1):
                p = Point(x, y)
                if polygon.contains(p):
                    volume_coords.append((x, y))

        hull_coords = []
        corners = list(zip(polygon.exterior.xy[0], polygon.exterior.xy[1]))
        for idx in range(len(corners) - 1):
            p1 = corners[idx]
            p2 = corners[idx + 1]
            x1 = int(p1[0])
            x2 = int(p2[0])
            y1 = int(p1[1])
            y2 = int(p2[1])
            xdiff = x2 - x1
            ydiff = y2 - y1

            # Find the line's equation, y = mx + b
            if xdiff != 0:
                m = ydiff / xdiff
            else:
                m = 1
            b = y1 - m * x1

            for xval in range(x1 + 1, x2):
                yval = int(m * xval + b)
                if int(yval) == yval:
                    hull_coords.append((xval, yval))

        return hull_coords, volume_coords

    def _get_area_tiles(self, volume_coords, hull_coords, doors, generate_walls, settings):
        area_objs = []
        area_nr = 0
        door_objs = []
        door_nr = 0
        wall_objs = []
        wall_nr = 0

        # Get the are name
        area_name = settings['name']

        # Get the area class (if known)
        class_name = settings['area_class']
        area_class = self._get_class(class_name, Area)
        area_kwargs = settings['area_kwargs']

        # Get the visualisation properties
        vis_prop = settings['visualisation_properties']
        area_vis = vis_prop['area']
        walls_vis = vis_prop['walls']

        # Create all area objects
        for area_coord in volume_coords:
            area_tile = self.get_area_tile(area_nr, area_name, area_coord, area_class, area_kwargs,
                                           settings['area_properties'], area_vis)
            area_nr += 1
            area_objs.append(area_tile)

        # If we do not need to generate walls, we add area tiles to the edges and return those, and no walls or doors
        if not generate_walls:
            for hull_coord in hull_coords:
                area_tile = self.get_area_tile(area_nr, area_name, hull_coord, area_class, area_kwargs,
                                               settings['area_properties'], area_vis)
                area_nr += 1
                area_objs.append(area_tile)

            return area_objs, [], []

        # Else we add walls and potential doors and return those as well
        for hull_coord in hull_coords:
            if hull_coord not in doors:
                wall_tile = self.get_area_tile(wall_nr, area_name, hull_coord, Wall, {}, {}, walls_vis)
                wall_nr += 1
                wall_objs.append(wall_tile)
            else:
                door_tile = self.get_area_tile(door_nr, area_name, hull_coord, Door, {}, {}, {})
                door_nr += 1
                door_objs.append(door_tile)

        return area_objs, wall_objs, door_objs

    def get_area_tile(self, nr, area_name, coord, callable_class, kwargs, properties, vis_properties):
        obj_id = f"{area_name}_{callable_class}_{nr}"

        obj_properties = self._add_missing_keys(properties, vis_properties)

        tile = callable_class(obj_id, area_name, locations=coord, properties=obj_properties, **kwargs)

        return tile
