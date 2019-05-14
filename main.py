from agents.Agent import Agent
from environment.objects.simple_objects import Wall, Battery
from scenario_manager.world_factory import WorldFactory, RandomProperty

if __name__ == "__main__":
    factory = WorldFactory(random_seed=1, shape=[10, 10], tick_duration=0.5)

    random_prop = RandomProperty(property_name="random_prop", values=["One", "Two"], distribution=[3, 1])
    factory.add_env_object(location=[0, 0], name="Wall 1", random_prop=random_prop)

    agent = Agent()
    factory.add_agent(location=[1, 0], agent=agent)

    world = factory.get_world()

    world.run()
