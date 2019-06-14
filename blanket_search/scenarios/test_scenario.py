from scenario_manager.world_factory import WorldFactory, RandomProperty
from agents.agent import Agent
from environment.objects.simple_objects import C4I, SeWaCo, Mobiliteit, Energy, Brand, Gewonde, Lekkage, Waypoint


def create_factory(seed=None):
    factory = WorldFactory(random_seed=seed, shape=[5, 5], tick_duration=0.5)

    random_prop = RandomProperty(values=["klein", "middelmatig", "groot"],
                                 distribution=[0.33, 0.33, 0.33])

    c4i_prob = 1.0
    energy_prob = 1.0
    lekkage_prob = 1.0
    sewaco_prob = 1.0
    gewonde_prob = 1.0
    brand_prob = 1.0
    mobiliteit_prob = 1.0

    factory.add_env_object_prospect(location=[0, 0], name="C4I", callable_class=C4I, probability=c4i_prob,
                                    omvang=random_prop)
    factory.add_env_object_prospect(location=[1, 0], name="C4I", callable_class=C4I, probability=c4i_prob,
                                    omvang=random_prop)
    factory.add_env_object_prospect(location=[2, 0], name="C4I", callable_class=C4I, probability=c4i_prob,
                                    omvang=random_prop)

    factory.add_env_object_prospect(location=[0, 1], name="Gewonde", callable_class=Gewonde, probability=gewonde_prob,
                                    omvang=random_prop)
    factory.add_env_object_prospect(location=[1, 1], name="Gewonde", callable_class=Gewonde, probability=gewonde_prob,
                                    omvang=random_prop)
    factory.add_env_object_prospect(location=[2, 1], name="Gewonde", callable_class=Gewonde, probability=gewonde_prob,
                                    omvang=random_prop)

    factory.add_env_object_prospect(location=[0, 2], name="Brand", callable_class=Brand, probability=brand_prob,
                                    omvang=random_prop)
    factory.add_env_object_prospect(location=[1, 2], name="Brand", callable_class=Brand, probability=brand_prob,
                                    omvang=random_prop)
    factory.add_env_object_prospect(location=[2, 2], name="Brand", callable_class=Brand, probability=brand_prob,
                                    omvang=random_prop)

    factory.add_env_object_prospect(location=[0, 3], name="SeWaCo", callable_class=SeWaCo, probability=sewaco_prob,
                                    omvang=random_prop)
    factory.add_env_object_prospect(location=[1, 3], name="SeWaCo", callable_class=SeWaCo, probability=sewaco_prob,
                                    omvang=random_prop)
    factory.add_env_object_prospect(location=[2, 3], name="SeWaCo", callable_class=SeWaCo, probability=sewaco_prob,
                                    omvang=random_prop)

    factory.add_env_object_prospect(location=[0, 4], name="Energy", callable_class=Energy, probability=energy_prob,
                                    omvang=random_prop)
    factory.add_env_object_prospect(location=[1, 4], name="Energy", callable_class=Energy, probability=energy_prob,
                                    omvang=random_prop)
    factory.add_env_object_prospect(location=[2, 4], name="Energy", callable_class=Energy, probability=energy_prob,
                                    omvang=random_prop)

    agent = Agent()
    factory.add_agent(location=[1, 0], agent=agent)
    agent = Agent()
    factory.add_agent(location=[2, 0], agent=agent)

    return factory