class Goal:

    # a task describes a subgoal to be accomplished as part of the mission
    # a task has a unique identifier, a name, a priority and is assigned
    # to an agent
    def __init__(self, goal_id, goal_location, goal_class, task_model):

        self.goal_id = goal_id
        self.goal_type = goal_class
        if self.goal_type not in task_model.possible_goals:
            print("Error: goal type not known in task model")
        self.goal_location = goal_location
        self.actions = []
        self.required_skills = []
        self.priority = None
        self.build_goal(task_model)

    # assign task priority to this task, based on the task model.
    def build_goal(self, task_model):
        self.actions = task_model.goal_action_dependencies[self.goal_type]
        for action in self.actions:
            self.required_skills = task_model.action_skill_dependencies[action]
        self.priority = task_model.strategy[self.goal_type]

    def equals(self, obj):
        if not isinstance(obj, Goal):
            return False
        if obj.goal_id != self.goal_id:
            return False
        if obj.goal_location != self.goal_location:
            return False
        if obj.priority != self.priority:
            return False
        return True

    def __str__(self):
        return "ID: " + str(self.goal_id) + " Type: "+str(self.goal_type) + " Location: " + str(self.goal_location["location"])
        #return str(self.__dict__)
