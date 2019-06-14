from environment.actions.object_actions import RemoveObject
from modules.TaskModel import TaskModel
from modules.goal import Goal
from environment.objects.env_object import EnvObject
import numpy as np


class GoalTranslator:

    def __init__(self, task_model: TaskModel):
        self.model_name = task_model.model_name
        self.translation_dict = task_model.goal_translation

    def translate(self, goal: Goal):
        # Get environment object that makes up the goal and take its ID
        env_obj = goal.goal_location
        obj_id = env_obj["obj_id"]

        # Get the actions that need to be applied on the object to accomplish the goal
        translated_actions = self.translation_dict[goal.goal_type]

        # Translate each goal action to a string according to the translation dict obtained from the TaskModel. These
        # strings represent either an identifier the agent should parse into GridWorld actions or directly the name of
        # a GridWorld action. The translation dictionary also contains any default arguments for that action.
        new_translated_actions = []
        for action_name, action_args in translated_actions:
            # We always append the object id to the action arguments list, as we define goals on a set of actions that
            # apply to an EnvObject
            action_args["object_id"] = obj_id

            # We append the action name and arguments to the list of translations
            new_translated_actions.append((action_name, action_args))

        # Return the action name and arguments
        return translated_actions