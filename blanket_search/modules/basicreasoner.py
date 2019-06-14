from blanket_search.modules.goal import Goal
from blanket_search.modules.translator import GoalTranslator


class BasicReasoner:

    # the BasicReasoner allows for reasoning about an agent's todo list and
    # provides the goal in the todo list that currently has the highest
    # priority based on the strategy
    def __init__(self, task_model, previous_observations, current_observations, agentnumber):
        self.task_model = task_model
        # Create the translator
        self.translator = GoalTranslator(task_model)
        # todo_list_prios is een dict van alle goal objects met hun bijbehorende prioriteit
        self.todo_list_prios = {}
        # prio_goals is een lijst van de goals met de hoogste prio in de totale lijst todo_list_prios
        # dat wil zeggen: als er meerdere brandjes zijn, die de hoogst mogelijke prio hebben (bijv. 0)
        # dan bestaat prio-goals uit een lijstje van enkel alle brandjes (met allemaal prio 0)
        # todo: bepalen welke van de bekende objecten met gelijke prio dan als eerste moet worden
        # afgehandeld
        # prio_goals is dus een manier om op te lossen dat er soms meerdere objecten bestaan met gelijke
        # prio en je dan daarover weer een prio moet bepalen obv hun locatie.
        self.prio_goals = []
        self.route_name = 'Route ' + str(agentnumber)
        self.prio_goal = None
        if current_observations is not None:
            self.update_todos(previous_observations, current_observations)

    def update_todos(self, previous_observations, current_observations):
        self.todo_list_prios = {}
        self.prio_goals = []
        self.add_todos(current_observations)
        # todo: verwerken van inkomende state verandering
        # bepalen welke elementen in de state moeten worden omgezet naar een nieuw goal in de todo list
        # bepalen welke elementen in de state ertoe leiden dat een goal uit de todo list moet worden
        # verwijderd
        # gebruik maken van onderstaande functies (add en remove todos) om de todolist te updaten

    def add_todos(self, goal_id_location_list):
        for goal_id in goal_id_location_list:
            classname = goal_id_location_list[goal_id]["class_inheritance"][0]
            if classname in self.task_model.possible_goals:
                if classname != 'Waypoint' or goal_id_location_list[goal_id]["route_name"] == self.route_name:  
                    new_goal = Goal(goal_id, goal_id_location_list[goal_id],
                                classname, self.task_model)
                    self.todo_list_prios[new_goal] = new_goal.priority

        #Als er niets te doen is voor deze agent, dan klaar
        if len(self.todo_list_prios) == 0:
            self.prio_goal=None
            return None

        highest_prio = min(self.todo_list_prios,
                           key=self.todo_list_prios.get)
        print(highest_prio.goal_id)
        self.prio_goals = (k for k, v in self.todo_list_prios.items() if float(v) <= self.todo_list_prios[highest_prio])
        
        prio_goals_filtered = {}

        for goal in self.prio_goals:
            if goal.goal_type == "Waypoint":
                if goal.goal_location["route_name"] == self.route_name:
                    prio_goals_filtered[goal.goal_location['obj_id']] = goal
            else:
                self.prio_goal = goal
                return goal
                    # if self.prio_goal.goal_type == "Waypoint":
                    #    get next waypoint from walking route

        waypointnumber = 1000
        bestgoal = None
        for key, goal in prio_goals_filtered.items():
            if goal.goal_location["waypoint_number"] < waypointnumber:
                waypointnumber = goal.goal_location["waypoint_number"]
                bestgoal = goal
        #self.prio_goal = min(prio_goals_filtered, key=prio_goals_filtered.values()["waypoint_number"])
            #Todo remove object op waypoint? in de search aktie
        self.prio_goal = bestgoal
        return bestgoal

    def remove_todos(self, goals):
        for goal in goals:
            self.todo_list_prios.pop(goal)
            #self.todo_list_prios.remove(goal)
            #self.todo_list_suggest.pop(goal.goal_id)
            #for agent_name, mental_model in self.mental_models.items():
            #    mental_model.goal_effectiveness.pop(goal.goal_id)

    def request_current_goal(self):
        return self.prio_goal

    def translate_goal_to_action(self, goal: Goal):
        # Call the translator
        return self.translator.translate(goal=goal)
