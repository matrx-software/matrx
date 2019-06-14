from environment.actions.move_actions import Move
from environment.actions.object_actions import RemoveObject
from modules.TaskModel import TaskModel


class BS_TaskModel:

    @staticmethod
    def create_bs_task_model():
        task_model_name = "BS_task"

        possible_goals = ["Waypoint",
                          "Brand",
                          "Lekkage",
                          "Gewonde",
                          "C4I",
                          "SeWaCo",
                          "Mobiliteit",
                          "Energy"]

        possible_actions = {"fire_fighting": [10, 30, 50],
                            "leak_stop": [20, 40, 60],
                            "assist_injured": [60, 60, 60],
                            "repair_c4i": [40, 80, 160],
                            "repair_sewaco": [40, 80, 160],
                            "repair_mobility": [40, 80, 160],
                            "repair_energy": [40, 80, 160],
                            "move": [10, 10, 10],
                            "search_room": [10, 10, 10],
                            "perceive": [0, 0, 0],
                            "send_message": [1, 1, 1]}

        possible_skills = ["fire_skill",
                           "leak_skill",
                           "assist_skill",
                           "c4i_skill",
                           "sewaco_skill",
                           "mobility_skill",
                           "energy_skill",
                           "basic_action_skill"]

        goal_action_dependencies = {"Waypoint": ["perceive", "search"],
                                    "Brand": ["fire_fighting"],
                                    "Lekkage": ["leak_stop"],
                                    "Gewonde": ["assist_injured"],
                                    "C4I": ["repair_c4i"],
                                    "SeWaCo": ["repair_sewaco"],
                                    "Mobiliteit": ["repair_mobility"],
                                    "Energy": ["repair_energy"]}

        # Translation currently only supports 'RemoveObject' action and any custom string an agent supports itself
        goal_action_translation = {"Waypoint": [("search", {}), (RemoveObject.__name__, {"remove_range": 1})],
                                    "Brand": [(RemoveObject.__name__, {"remove_range": 1})],
                                    "Lekkage": [(RemoveObject.__name__, {"remove_range": 1})],
                                    "Gewonde": [(RemoveObject.__name__, {"remove_range": 1})],
                                    "C4I": [(RemoveObject.__name__, {"remove_range": 1})],
                                    "SeWaCo": [(RemoveObject.__name__, {"remove_range": 1})],
                                    "Mobiliteit": [(RemoveObject.__name__, {"remove_range": 1})],
                                    "Energy": [(RemoveObject.__name__, {"remove_range": 1})]}

        action_skill_dependencies = {"fire_fighting": ["fire_skill"],
                                     "leak_stop": ["leak_skill"],
                                     "assist_injured": ["assist_skill"],
                                     "repair_c4i": ["c4i_skill"],
                                     "repair_sewaco": ["sewaco-skill"],
                                     "repair_mobility": ["mobility_skill"],
                                     "repair_energy": ["energy_skill"],
                                     "move": ["basic_action_skill"],
                                     "search": ["basic_action_skill"],
                                     "perceive": ["basic_action_skill"],
                                     "send_message": ["basic_action_skill"]}

        strategy = {"Brand": 0, "Lekkage": 1, "Gewonde": 2,
                    "Waypoint": 3,
                    "C4I": 4, "SeWaCo": 4, "Mobiliteit": 4, "Energy": 4}

        task_model = TaskModel(task_model_name, possible_goals, goal_action_translation,
                               possible_actions, possible_skills,
                               goal_action_dependencies,
                               action_skill_dependencies, strategy)

        return task_model
