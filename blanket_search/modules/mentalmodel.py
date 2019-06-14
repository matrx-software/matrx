class MentalModel:

    # a mental model contains information about a certain agent"s capabilities
    # along with its current activity and an ordered dict displaying the
    # agent"s potential activities ordered according to where it would be at
    # its most effective to where it would be least effective
    def __init__(self, owner_name, task_model, name, skills, todo_list):
        self.owner_name = owner_name
        self.task_model = task_model
        self.agent_name = name
        self.skills = skills
        self.goal_effectiveness = {}
        self.assign_goal_effects(todo_list)

    # the update_model function is used to update the mental models when new
    # information has been gathered about a team mate"s capabilities.
    def update_skills(self, newskills, todo_list):
        for newskill in newskills:
            self.skills[newskill] = newskills[newskill]

        # print("assign new task priority for " + self.agent_name)
        self.assign_goal_effects(todo_list)
        # print(self.todo_list[0].task_type)

    # the assign_goal_priority function decides what would be the most
    # effective goal for this particular agent to perform given this agent"s
    # capabilities and the priority of the tasks given the chosen strategy.
    # the agent would be most effective when working on the highest
    # prioritized goal, at which the agent has a high capability. So
    # we have to match priority and capability here and return the highest
    # value, then the second highest, and so on, resulting in an ordered
    # list. For this, we use the task model and the mental model.
    def assign_goal_effects(self, todo_list):
        for goal in todo_list:
            for skill in goal.required_skills:
                effectiveness = self.skills[skill]/(goal.priority+1)
                self.goal_effectiveness[goal.goal_id] = effectiveness

    def find_max_goal_value(self):
        goal_priorities = {}
        ge = self.goal_effectiveness
        max_value = ge[max(ge, key=self.goal_effectiveness.get)]
        for goal in self.goal_effectiveness:
            if self.goal_effectiveness[goal] == max_value:
                goal_priorities.append(goal)
        return goal_priorities
