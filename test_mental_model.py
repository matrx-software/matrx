from modules.mentalmodelreasoner import MentalModelReasoner
from scenario_manager.scenarios.bstaskmodel import BS_TaskModel
# from environment.objects.basic_objects import AgentObject

# initialize a task and mental model with potential tasks, potential
# capabilities, dependencies between tasks and capabilities, agents and their
# characteristics, and a strategy

task_model = BS_TaskModel.create_bs_task_model()


def print_information():
    for goal_id in mm_reasoner.todo_list_prios:
        for agent_name, mental_model in mm_reasoner.mental_models.items():
            print(agent_name + " has goal effectiveness "
                  + str(mental_model.goal_effectiveness[goal_id])
                  + " for goal " + goal_id)
        best_agent = mm_reasoner.todo_list_suggest[goal_id]
        mental_model = mm_reasoner.mental_models[best_agent]
        print("The best agent to perform " + goal_id + " is "
              + best_agent + " as this agent's skill "
              + "for this goal type is: "
              + str(mental_model.goal_effectiveness[goal_id]))


agents = [{"name": "agent_1",
           "skills": {"sewaco_skill": 1,
                      "mobility_skill": 0.1,
                      "c4i_skill": 0.1,
                      "energy_skill": 0.1,
                      "fire_skill": 0.5,
                      "leak_skill": 0.5,
                      "assist_skill": 1,
                      "basic_action_skill": 1}},
          {"name": "agent_2",
           "skills": {"sewaco_skill": 0.1,
                      "mobility_skill": 1,
                      "c4i_skill": 0.1,
                      "energy_skill": 0.1,
                      "fire_skill": 0.6,
                      "leak_skill": 0.5,
                      "assist_skill": 0.8,
                      "basic_action_skill": 1}},
          {"name": "agent_3",
           "skills": {"sewaco_skill": 0.1,
                      "mobility_skill": 0.1,
                      "c4i_skill": 1,
                      "energy_skill": 0.1,
                      "fire_skill": 0.4,
                      "leak_skill": 0.5,
                      "assist_skill": 0.9,
                      "basic_action_skill": 1}}]

goal_id_location_list = {"Brand1": "room1",
                         "Brand2": "room2",
                         "Gewonde1": "room2"}

mm_reasoner = MentalModelReasoner("agent_1", task_model,
                                  goal_id_location_list, agents)
print_information()

mm_reasoner.update_mental_models([{"name": "agent_1",
                                  "skills": {"fire_skill": 0.1,
                                             "assist_skill": 0.1}}])

print(" ")
print("|||---after reducing the capabilities of agent 1:---|||")
print(" ")
print_information()

newly_observed_tasks = {"Brand3": "room3",
                        "Gewonde2": "room4",
                        "Gewonde3": "room3"}
mm_reasoner.add_todos(newly_observed_tasks)

print(" ")
print("|||---after adding three new events to the todo list:---|||")
print(" ")
print_information()

mm_reasoner.remove_todos([mm_reasoner.todo_list[0]])

print(" ")
print("|||---after removing the first event from the todo list:---|||")
print(" ")
print_information()
