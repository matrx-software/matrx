from scenario_manager.scenarios.bstaskmodel import BS_TaskModel
from modules.basicreasoner import BasicReasoner
# from environment.objects.basic_objects import AgentObject

# initialize a task and mental model with potential tasks, potential
# capabilities, dependencies between tasks and capabilities, agents and their
# characteristics, and a strategy


task_model = BS_TaskModel.create_bs_task_model()

goal_id_location_list = {"Brand1": "room1",
                         "Brand2": "room2",
                         "Gewonde1": "room2"}


basic_reasoner = BasicReasoner(task_model, goal_id_location_list)
