import numpy as np
import json

from agents.capabilities.capability import SenseCapability
from agents.agent import Agent
from agents.waypointnavigator import WaypointNavigator
from modules.basicreasoner import BasicReasoner
from scenario_manager.scenarios.bstaskmodel import BS_TaskModel
from environment.actions.move_actions import *
from environment.actions.object_actions import *
from environment.objects.simple_objects import *


class BSAgent(Agent):
    AGENT_PROPERTIES_JSON = "scenario_manager/scenarios/bs_agent_properties.json"
    bs_action_set = [
        MoveNorth.__name__,
        MoveNorthEast.__name__,
        MoveEast.__name__,
        MoveSouthEast.__name__,
        MoveSouth.__name__,
        MoveSouthWest.__name__,
        MoveWest.__name__,
        MoveNorthWest.__name__,
        RemoveObject.__name__]

    def __init__(self, nr_agent: int):
        super(BSAgent, self).__init__()
        with open(self.AGENT_PROPERTIES_JSON, "r") as f:
            all_props = json.load(f)

        self.nr_agent = nr_agent
        self.name = f"agent_{nr_agent}"
        self.skills = all_props['agents'][self.name]['skills']
        self.action_durations = all_props['action_durations']
        # self.bs_actions = all_props[self.name]['action_durations'].keys()
        self.action_durations = all_props['action_durations']
        senses = {None: np.inf}
        self.sense_capability = SenseCapability(senses)
        self.all_observed_entities = {}
        self.previous_observed_entities = {}
        self.busy_with_action = False

        self.navigator = WaypointNavigator(self.agent_id)
        self.last_action = ''
        self.current_state = None
        self.current_goal = None
        self.previous_goal = None
        self.taskmodel = BS_TaskModel.create_bs_task_model()
        self.basicreasoner = BasicReasoner(self.taskmodel, None, None, self.nr_agent)
        

    def ooda_observe(self, state):
        """
        During the observe phase, the BS-agent performs its perceive-action, by which it identifies all incidents that
        can be sensed by this agent. The perceive-action is free and is performed at every tick. This allows the agent
        to change its plan based on its percepts within one tick.

        :param state:
        :return: current state, previous state, delta state
        """
        self.previous_observed_entities = self.all_observed_entities

        # on the first tick, look for the waypoints that belong to this agent, and add them to the observed entities.
        for key, env_obj in state.items():
            if Waypoint.__name__ in env_obj["class_inheritance"]:
                if env_obj["route_name"] == "Route " + str(self.nr_agent):
                    self.all_observed_entities[env_obj['obj_id']] = env_obj

        # if last_action is Search, than retrieve the complete state, including system defects at the location of the
        # agent.
        if str(self.last_action).lower() != 'search':
            current_location = self.agent_properties['location']
            for entity, entity_details in state.copy().items():
                # if perceived entity is at the same location as the agent (except agent itself)
                if entity_details['location'] == current_location:
                    # if perceived entity has a category which is an storing
                    if C4I.__name__.lower() != entity_details['class_inheritance'][0].lower() and \
                            SeWaCo.__name__.lower() != entity_details['class_inheritance'][0].lower() and \
                            Energy.__name__.lower() != entity_details['class_inheritance'][0].lower() and \
                            Mobiliteit.__name__.lower() != entity_details['class_inheritance'][0].lower():
                            self.all_observed_entities[entity] = entity_details
                        #state.pop(entity)
        else:
            current_location = self.agent_properties['location']
            for entity, entity_details in state.copy().items():
                # if perceived entity is at the same location as the agent (except agent itself)
                if entity_details['location'] == current_location:
                    # if perceived entity has a category which is an storing
                        self.all_observed_entities[entity] = entity_details

        #Remove all observations that are not present in the world any longer, for example bevause a fire is extinguished
        #TODO: when other agents remove an object, we magically know that it is gone
        for key, env_obj in self.all_observed_entities.copy().items():
            if key not in state.keys():
                self.all_observed_entities.pop(key)

        self.current_state = state

        return self.all_observed_entities

    def ooda_orient(self, state):
        """
        During the orient phase, the agent

        :param state:
        :return:
        """
        return state

    def ooda_decide(self, previous_observations, current_observations, possible_actions):
        """
        For now, choose a random action from all possible actions
        In our implementation, we determine the action for each agent in the Plan class
        The duration of actions should be determined based on the object on which the action is performed (its 'size')

        Pseudo-code (based on discussion 21-5-2019):
        ------------------------------
        If the agent is performing an action that takes time, or does not have an action, do nothing
        ------------------------------
            if wait:
                return None
        ------------------------------
        If the reasoner wants to reassign tasks to this agent (e.g., because there is new information),
        than it should determine a new task for this agent, which should be translated into actions that are required
        for this task. The waypoint navigator then determines the next move action for the agent.
        ------------------------------
            if reasoner has update:
                task = reasoner.get_task(current_state, previous_state)
                actions, kwargs = translator.translate(task, state)
                waypoint_nav.reset()
                waypoint_nav.add_waypoint(action, kwargs)

            next_action, kwargs = waypoint_nav.get_next_action()
            previous_state = state
            current_state = None
            previous_action = next_action
            if next_action == 'search':
                next_action = None

            return next_action, kwargs

        """
        self.previous_goal = self.current_goal
        possible_actions.append('search')

        if possible_actions:
            # todo: get action from the Plan class
            # todo: check if previous action did not succeed. If yes, stop performing this action

            # if agent is not already performing an action, determine the action to perform
            if not self.busy_with_action:

                print ("deciding")
                
                self.basicreasoner.update_todos(previous_observations, current_observations)
                self.current_goal = self.basicreasoner.request_current_goal()
                print("Current goal: " + str(self.current_goal))
                
                #When there is nothing to do for us, return None
                if self.current_goal == None: 
                    return None, {}

                if not self.current_goal.equals(self.previous_goal) or self.navigator.is_finished():
                    action_list = self.basicreasoner.translator.translate(self.current_goal)
                    self.navigator = WaypointNavigator(self.agent_id)
                    for action, action_arguments in action_list:
                        self.navigator.add_waypoint(self.current_goal.goal_location["location"][0],self.current_goal.goal_location["location"][1], action = action, action_kwargs=action_arguments)
                
                action_name, args = self.navigator.next_basic_action(agent_state=current_observations, possible_actions=possible_actions)

                print("Performing action: "+action_name)

                # get duration of the action
                print(">>>>>>>" + action_name.lower())
                if 'move' in action_name.lower() and not 'remove' in action_name.lower():
                    action_duration = self.taskmodel.possible_actions["move"][0]
                elif 'search' in action_name.lower():
                    action_duration = self.taskmodel.possible_actions["search_room"][0]
                elif 'message' in action_name.lower():
                    action_duration = self.taskmodel.possible_actions["send_message"][0]

                # else, the action involves removing an object (resolve incident/defect)
                # todo: add remove action after determining the object_id on which the action is performed (look at
                # todo: RemoveObject above)
                else:
                    if 'removeobject' in action_name.lower():
                        #if ("Route 5-4_46" == args["object_id"]):
                        #    self.basicreasoner.update_todos(previous_observations, current_observations)
                        #    self.current_goal = self.basicreasoner.request_current_goal()
                        object_of_interest = current_observations[args["object_id"]]
                        if object_of_interest["class_inheritance"][0] == "Waypoint":
                            action_duration = 0

                        else:
                            if object_of_interest["omvang"]=="klein":
                                incident_size = 0
                            if object_of_interest["omvang"]=="middelmatig":
                                incident_size = 1
                            if object_of_interest["omvang"]=="groot":
                                incident_size = 2

                            if object_of_interest["class_inheritance"][0] == "Brand":
                                action_duration = self.taskmodel.possible_actions["fire_fighting"][incident_size]
                            elif object_of_interest["class_inheritance"][0] == "Lekkage":
                                action_duration = self.taskmodel.possible_actions["leak_stop"][incident_size]
                            elif object_of_interest["class_inheritance"][0] == "Gewonde":
                                action_duration = self.taskmodel.possible_actions["assist_injured"][incident_size]
                            elif object_of_interest["class_inheritance"][0] == "C4I":
                                action_duration = self.taskmodel.possible_actions["repair_c4i"][incident_size]
                            elif object_of_interest["class_inheritance"][0] == "Energy":
                                action_duration = self.taskmodel.possible_actions["repair_energy"][incident_size]
                            elif object_of_interest["class_inheritance"][0] == "SeWaCo":
                                action_duration = self.taskmodel.possible_actions["repair_sewaco"][incident_size]
                            elif object_of_interest["class_inheritance"][0] == "Mobiliteit":
                                action_duration = self.taskmodel.possible_actions["repair_mobility"][incident_size]
                        
                        self.basicreasoner.remove_todos([self.current_goal])

                self.action_time_left = action_duration - 1
                self.busy_with_action = True
                self.performing_action = action_name

                # We check if the last action is a Search action. If so, than the agent should stay idle (action = none).
                # In the next Observe phase, the agent searches for system defects.
                self.last_action = action_name
                if action_name == 'search':
                    action_name = None

                print(f"{self.name} performs action {action_name}")
                return action_name, args

            else:
                action = None
                # agent is already performing an action
                if self.action_time_left > 1:
                    self.action_time_left -= 1
                # agent finished the action
                else:
                    self.busy_with_action = False
                    print(f"{self.name} performs action {action}")
                    return action, {}

            print(f"{self.name} performs action {action}")
            return action, {}
                
