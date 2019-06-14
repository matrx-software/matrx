from agents.agent import Agent
from blanket_search.bsagent import BSAgent
from scenario_manager.world_factory import WorldFactory, RandomProperty


def create_factory():
    factory = WorldFactory(random_seed=1, shape=[10, 10], tick_duration=0.1)
    
    # TODO set random properties and distributions
    random_prop = RandomProperty(values=["Geen", "Dit", "Of", "Dat"],
                                 distribution=[0.5, 0.1, 0.15, 0.25])
    factory.add_env_object(location=[0, 0], name="Wall 1", random_prop=random_prop)

    # TODO add more of those objects with the correct distributions


    agent = Agent()  # Change to BS agent
    factory.add_agent(location=[1, 0], agent=agent)
    factory.add_env_object(location=[0, 1], name="Route 1-1", is_traversable=True, visualize_size=0.2, is_route_obj=True)
    factory.add_env_object(location=[0, 2], name="Route 1-2", is_traversable=True, visualize_size=0.2, is_route_obj=True)
    factory.add_env_object(location=[0, 3], name="Route 1-3", is_traversable=True, visualize_size=0.2, is_route_obj=True)
    factory.add_env_object(location=[0, 4], name="Route 1-4", is_traversable=True, visualize_size=0.2, is_route_obj=True)

    #factory.add_env_object(location=[1,0], name="Brand1", callable_class=Brand)
    #factory.add_env_object(location=[1, 0], name="Route 1-1", is_traversable=True, visualize_size=0.2, is_route_obj=True)
    #factory.add_env_object(location=[0, 2], name="Route 1-2", is_traversable=True, visualize_size=0.2, is_route_obj=True)
    #factory.add_env_object(location=[0, 3], name="Route 1-3", is_traversable=True, visualize_size=0.2, is_route_obj=True)
    #factory.add_env_object(location=[0, 4], name="Route 1-4", is_traversable=True, visualize_size=0.2, is_route_obj=True)

    agent_1 = BSAgent(nr_agent=1)  # Change to BS agent
    factory.add_agent(location=[1, 0], agent=agent_1, name=agent_1.name, possible_actions=BSAgent.bs_action_set,
                      sense_capability=agent_1.sense_capability)

    # TODO add more agents
    # TODO create task model, containing relations between actions and skills

    return factory
