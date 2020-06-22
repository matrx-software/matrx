from matrx.agents import AgentBrain


class BlockWorldAgent(AgentBrain):

    def __init__(self, memorize_for_ticks=10):
        self.__memorize_for_ticks = memorize_for_ticks
        self.__collect = None
        super().__init__()

    def initialize(self):
        pass

    def filter_observations(self, state_dict):
        self.state[self.agent_id]
        self.state["foo"]
        self.state[["Collect block_585", "Collect block_586"]]
        self.state[{"foo": "bar"}]
        self.state["is_open"]
        self.state[{"room_name": "room_0"}]
        self.state[{"room_name": "room_0", "class_inheritance": "Wall"}]
        self.state[{"room_name": ["room_0", "room_1"]}]
        self.state[{"room_name": ["room_0", "room_1"], "class_inheritance": "Wall"}]
        self.state[{"room_name": ["room_0", "room_1"], "class_inheritance": ["Wall", "Door"]}]
        self.state[{"room_name": ["room_0", "room_1"], "is_open": True}]

        self.state.get_world_info()
        self.state.get_agents()
        self.state.get_room_doors()
        self.state.get_with_property()
        self.state.get_room_content()
        self.state.get_all_room_names()
        self.state.get_room_objects()
        self.state.get_agents_with_property()
        self.state.get_closest_agents()
        self.state.get_closest_objects()
        self.state.get_closest_room_door()
        self.state.get_closest_with_property()
        self.state.get_distance_map()
        self.state.get_of_type()
        self.state.get_team_members()
        self.state.get_traverse_map()
        self.state.get_with_colour()
        self.state.get_with_depth()
        self.state.get_with_shape()
        self.state.get_with_opacity()
        self.state.get_with_size()
        self.state.apply_occlusion()
        self.state.remove_with_property()

        if self.__collect is None:
            pass
        return self.state.as_dict()

    def decide_on_action(self, state_dict):
        return None, {}
