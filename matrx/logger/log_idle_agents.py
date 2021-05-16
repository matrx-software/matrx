from matrx.logger.logger import GridWorldLogger, GridWorldLoggerV2


class LogIdleAgents(GridWorldLogger):
    """ Logs the number of idle agents per tick """

    def __init__(self, log_strategy=1, save_path="", file_name_prefix="", file_extension=".csv", delimeter=";"):
        super().__init__(log_strategy=log_strategy, save_path=save_path, file_name=file_name_prefix,
                         file_extension=file_extension, delimiter=delimeter)

    def log(self, grid_world, agent_data):
        log_statement = {}
        for agent_id, agent_obj in grid_world.registered_agents.items():
            idle = agent_obj.properties['current_action'] is None
            log_statement[agent_id] = int(idle)

        for agent_id, agent_obj in grid_world.registered_agents.items():
            if log_statement[agent_id] != 0:
                return log_statement

        return None


class LogIdleAgentsV2(GridWorldLoggerV2):
    """ Logs the number of idle agents per tick """

    def __init__(self, log_strategy=1, save_path="", file_name_prefix="", file_extension=".csv", delimeter=";"):
        super().__init__(log_strategy=log_strategy, save_path=save_path, file_name=file_name_prefix,
                         file_extension=file_extension, delimiter=delimeter)

    def log(self, world_state, agent_data, grid_world):
        log_statement = {}
        for agent_id, agent_obj in grid_world.registered_agents.items():
            idle = agent_obj.properties['current_action'] is None
            log_statement[agent_id] = int(idle)

        for agent_id, agent_obj in grid_world.registered_agents.items():
            if log_statement[agent_id] != 0:
                return log_statement

        return None
