import csv
import datetime
import os


class GridWorldLogger:
    LOG_ON_LAST_TICK = "log_last_tick"
    LOG_ON_FIRST_TICK = "log_first_tick"
    LOG_ON_GOAL_REACHED = "log_on_reached_goal"

    def __init__(self, log_strategy=1, save_path="/logs", file_name="", file_extension=".csv", delimiter=";"):
        self.__log_strategy = log_strategy
        self.__save_path = save_path
        self.__file_name_prefix = file_name
        self.__file_extension = file_extension
        self.__delimiter = delimiter

        # Create the file name
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.__file_name = f"{file_name}_{current_time}{file_extension}"

        self.__last_logged_tick = -1  # to track when we logged last
        self.__columns = []  # place holder for the columns in our data file
        self.__prev_goal_status = {}  # to track if a goal was accomplished since last call

    def log(self, grid_world, agent_data):
        return {}

    def _grid_world_log(self, grid_world, agent_data, last_tick=False, goal_status=None):
        if not self._needs_to_log(grid_world, last_tick, goal_status):
            return

        data = self.log(grid_world, agent_data)
        if data is None or data == {}:
            return

        self.__check_data(data)

        self.__write_data(data, grid_world.current_nr_ticks)

    def _needs_to_log(self, grid_world, last_tick, goal_status):
        current_tick = grid_world.current_nr_ticks

        # If the strategy is a tick frequency, check if enough ticks have passed
        if isinstance(self.__log_strategy, int):
            # the current nr ticks minus the tick we last logged should be smaller or equal to our frequency
            to_log = (current_tick - self.__last_logged_tick) >= self.__log_strategy
            if to_log:
                self.__last_logged_tick = current_tick

        # if the strategy is to log at the first tick, we do so if the current tick is zero
        elif self.__log_strategy == self.LOG_ON_FIRST_TICK:
            to_log = current_tick == 0

        # if the strategy is to log whenever one of the goals was reached
        elif self.__log_strategy == self.LOG_ON_GOAL_REACHED:
            to_log = False
            # we loop over all goals and see it's status became True whereas it was the previous time False
            for goal, status in goal_status.items():
                if goal in self.__prev_goal_status.keys():
                    if status and not self.__prev_goal_status[goal]:
                        to_log = True
                        break
            self.__prev_goal_status = goal_status.copy()

        # If we log on the last tick, only if the GridWorld says it is done
        elif self.__log_strategy == self.LOG_ON_LAST_TICK:
            to_log = last_tick

        # If the strategy is not found, we return an exception
        else:
            raise Exception(f"The log strategy {self.__log_strategy} is not recognized. Should be an integer or one of"
                            f"the GridWorld.ON_LOG_<...> values.")

        return to_log

    def _set_world_nr(self, world_nr):
        # Set the world number
        self.__world_nr = world_nr

        # Create the total file name path based on the world number (set by the WorldBuilder on logger creation)
        self.__save_path = f"{self.__save_path}{os.sep}world_{world_nr}"

        # Create the directory if not given
        if not os.path.exists(self.__save_path):
            os.makedirs(self.__save_path)

        self.__file_name = f"{self.__save_path}{os.sep}{self.__file_name}"

    def __check_data(self, data):
        if isinstance(data, dict):

            # Check if the data contains new columns, if so raise an exception that we cannot add columns on the fly
            if len(self.__columns) > 0:
                new_columns = set(data.keys()) - set(self.__columns)
                if len(new_columns) > 0:
                    raise Exception(f"Cannot append columns to the log file when we already logged with different "
                                    f"columns. THe following columns are new; {list(new_columns)}")

            return True
        else:
            raise Exception(f"The data in this {self.__class__} should be a dictionary.")

    def __write_data(self, data, tick_nr):

        # We always include the world number and the tick number
        if "world_nr" not in data.keys():
            data["world_nr"] = self.__world_nr
        if "tick_nr" not in data.keys():
            data["tick_nr"] = tick_nr

        # Check if we have columns to write to, this will be the order in which we write them
        if len(self.__columns) == 0:
            # Then we set the keys as column names
            self.__columns = list(data.keys())

        # Write the data to the file, create it when it does not exist and in that case write the columns as well
        if not os.path.isfile(self.__file_name):
            mode = "w+"
            write_columns = True
        else:
            mode = "a"
            write_columns = False

        with open(self.__file_name, mode=mode,  newline='') as data_file:
            csv_writer = csv.DictWriter(data_file, delimiter=self.__delimiter, quotechar='"',
                                        quoting=csv.QUOTE_MINIMAL, fieldnames=self.__columns)

            # Write columns if we need to
            if write_columns:
                csv_writer.writeheader()

            csv_writer.writerow(data)
