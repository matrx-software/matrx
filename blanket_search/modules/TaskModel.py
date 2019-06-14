class TaskModel:

    # a task model contains information about the dependencies between the
    # tasks to be executed (in order of priority) and the capabilities
    # possessed by the actors
    def __init__(self, model_name, possible_goals, goal_action_translation, possible_actions,
                 possible_skills, goal_action_dependencies,
                 action_skill_dependencies, strategy):

        # the modelname is a string
        self.model_name = model_name

        # possible incidents is a list that looks like this:
        # ["Injured", "C4I"]
        self.possible_goals = possible_goals

        # set the dictionary for translating a goal action(s) to a certain action(s) known to the GridWorld
        self.goal_translation = goal_action_translation

        # possible actions is a list that looks like this:
        # ['fire_fighting', 'assist_injured']
        self.possible_actions = possible_actions

        # possible skills is a list that looks like this:
        # ['fire_skill', 'assist_skill']
        self.possible_skills = possible_skills

        # incident_action_dependencies is a dict that looks like this:
        # {'Injured': ['assist_injured'],
        #  'Fire': ['fire_fighting']}
        #  For now, this is interpreted as: to handle a fire, one is ought
        #  to carry out the sequence of action in the list in that order.
        self.goal_action_dependencies = goal_action_dependencies

        # action_skill_dependencies is a dict that looks like this:
        # {'fire_fighting': ['fire_skill'],
        #  'assist_injured': ['assist_skill']}
        #  For now, this is interpreted as: to carry out the task "fire
        #  fighting" you need to rely on either one of the skills listed.
        self.action_skill_dependencies = action_skill_dependencies

        # a strategy is a dict that looks like:
        # ['extinguish_fire': 0,'tend_to_victim': 1]
        # Higher priorities have lower numbers, so 0 is highest priority
        self.strategy = strategy

    # def
