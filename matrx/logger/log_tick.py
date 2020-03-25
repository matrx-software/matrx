from matrx.logger.logger import GridWorldLogger


class LogDuration(GridWorldLogger):

    def __init__(self, save_path="", file_name_prefix="", file_extension=".csv", delimeter=";"):
        super().__init__(save_path=save_path, file_name=file_name_prefix, file_extension=file_extension,
                         delimiter=delimeter, log_strategy=self.LOG_ON_LAST_TICK)

    def log(self, grid_world, agent_data):
        log_statement = {
            "tick": grid_world.current_nr_ticks
        }

        return log_statement
