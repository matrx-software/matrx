from matrx.agents import AgentBrain


class BlockWorldAgent(AgentBrain):

    def __init__(self, memorize_for_ticks=10):
        self.__memorize_for_ticks = memorize_for_ticks
        self.__collect = None
        super().__init__()

    def initialize(self):
        pass

    def filter_observations(self, state_dict):
        self.state.state_update(state_dict)
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

        if self.__collect is None:
            pass
        return self.state.as_dict()

    def decide_on_action(self, state_dict):
        return None, {}
