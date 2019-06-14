from modules.mentalmodel import MentalModel
from modules.goal import Goal


class MentalModelReasoner:
    effectiveness_threshold = 0.1

    # the mentalmodelreasoner allows for reasoning about multiple mental models
    def __init__(self, own_name, task_model, goal_id_location_list, agents):
        self.own_name = own_name
        self.task_model = task_model
        self.mm_init_check = False
        self.todo_list = []
        self.todo_list_prios = {}
        self.prio_goal = None
        self.add_todos(goal_id_location_list)
        self.mental_models = self.init_mental_models(agents)
        self.todo_list_suggest = {}
        self.determine_task_division()

    def update_todos(self, previous_state, current_state):
        pass
        # todo: verwerken van inkomende state verandering
        # bepalen welke elementen in de state moeten worden omgezet naar een nieuw goal in de todo list
        # bepalen welke elementen in de state ertoe leiden dat een goal uit de todo list moet worden
        # verwijderd
        # gebruik maken van onderstaande functies (add en remove todos) om de todolist te updaten

    def add_todos(self, goal_id_location_list):
        for goal_id in goal_id_location_list:
            new_goal = Goal(goal_id, goal_id_location_list[goal_id],
                            self.task_model)
            self.todo_list.append(new_goal)
            self.todo_list_prios[new_goal.goal_id] = new_goal.priority

        self.prio_goal = min(self.todo_list_prios,
                             key=self.todo_list_prios.get)
        if self.mm_init_check:
            for agent_name, mental_model in self.mental_models.items():
                mental_model.assign_goal_effects(self.todo_list)
            self.determine_task_division()
        # if self.prio_goal.goal_type == "Waypoint":
        #    get next waypoint from walking route

    def remove_todos(self, goals):
        for goal in goals:
            self.todo_list_prios.pop(goal.goal_id)
            self.todo_list.remove(goal)
            self.todo_list_suggest.pop(goal.goal_id)
            for agent_name, mental_model in self.mental_models.items():
                mental_model.goal_effectiveness.pop(goal.goal_id)

    def init_mental_models(self, agents):
        new_mental_models = {}
        for agent in agents:
            mentmod = MentalModel(self.own_name, self.task_model,
                                  agent["name"], agent["skills"],
                                  self.todo_list)
            new_mental_models[agent["name"]] = mentmod
        self.mm_init_check = True
        return new_mental_models

    def update_mental_models(self, agents):
        for agent in agents:
            mental_model = self.mental_models[agent["name"]]
            mental_model.update_skills(agent["skills"], self.todo_list)
        self.determine_task_division()

    def add_agents(self, agents):
        for x in agents:
            mentmod = MentalModel(self.own_name, self.task_model, x,
                                  self.todo_list_prios)
            self.mental_models[x] = mentmod
        self.determine_task_division()

    def remove_agents(self, agent_name):
        for mm in self.mental_models:
            if mm.agent_name == agent_name:
                self.mental_models.pop(mm)
        self.determine_task_division()

    # the determine_task_division function is used to reason about all mental
    # models and determine what task division would be best for the team
    def determine_task_division(self):
        for goal in self.todo_list:
            best_agent = self.find_best_agent(goal.goal_id)
            self.todo_list_suggest[goal.goal_id] = best_agent

    def find_best_agent(self, goal_id):
        agent_effectiveness = {}
        for agent_name, mental_model in self.mental_models.items():
            effectiveness = mental_model.goal_effectiveness[goal_id]
            agent_effectiveness[agent_name] = effectiveness
        best_agent = max(agent_effectiveness,
                         key=agent_effectiveness.get)
        if(best_agent == self.own_name):
            return self.own_name
        if((agent_effectiveness[best_agent]
           - agent_effectiveness[self.own_name]) >
           MentalModelReasoner.effectiveness_threshold):
            return best_agent
        else:
            return self.own_name
        # todo: meenemen van de tijd die het kost om van plek te verwisselen
        # todo: communicatie naar andere agent om überhaupt van taak te kunnen verwisselen
        # todo: nadenken over hoe agents onderling bepalen of een wissel opportuun is

    def request_current_goal(self):
        return self.prio_goal
