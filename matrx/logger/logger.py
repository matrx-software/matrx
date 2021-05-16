import csv
import datetime
import os
import warnings


class GridWorldLogger:
    """ A class to log data during a running world.

    Loggers are meant to collect, process and write data to files during a running world. They can be added through
    the :func:`matrx.world_builder.WorldBuilder.add_logger` method. We refer to that method on how to add a logger
    to your world.

    Note that a world can have multiple loggers, each resulting in their own unique log file. So you have the
    option to create a single large log file with a single logger, or segment the data in some way over different
    files with multiple loggers. Another reason for more then one logger is a difference in logging strategy. For
    instance to have a logger that logs only at the start or end of the world and a logger that logs at every tick.

    Parameters
    ----------
    log_strategy : int, str (default: 1)
        When an integer, the logger is called every that many ticks. When a string, should be
        GridWorldLogger.LOG_ON_LAST_TICK, GridWorldLogger.LOG_ON_FIRST_TICK or GridWorldLogger.LOG_ON_GOAL_REACHED.
        Respectively for only logging on the last tick of the world, the first tick of the world or every time a
        goal is reached.
    save_path : str (default: "/logs")
        The default path were log files are stored. If the path does not exist, it is created. Otherwise log files
        are added to that path. If multiple worlds are ran from the same builder, the directory will contain
        sub-folders depicting the world's number (e.g., "world_1" for the first world, "world_2" for the second,
        etc.).
    file_name : str (default: "")
        The file name prefix. Every log file is always appended by the timestamp (Y-m-d_H:M:S) and the file
        extension. When an empty string, log file names will thus be only the timestamp.
    file_extension : str (default: ".csv")
        The file name extension to be used.
    delimiter : str (default: ";")
        The column delimiter to be used in the log files.

    .. deprecated:: 2.1.0
          `GridWorldLogger` will be removed in the future, it is replaced by
          `GridWorldLoggerV2` because the latter works with the
          :class:`matrx.agents.agent_utils.state.State` object.

    """

    """Log strategy to log on the last tick of a world."""
    LOG_ON_LAST_TICK = "log_last_tick"

    """Log strategy to log on the first tick of a world."""
    LOG_ON_FIRST_TICK = "log_first_tick"

    """Log strategy to log every time a goal is reached or completed."""
    LOG_ON_GOAL_REACHED = "log_on_reached_goal"

    def __init__(self, log_strategy=1, save_path="/logs", file_name="", file_extension=".csv", delimiter=";"):

        warnings.warn(
            f"{self.__class__.__name__} will be updated in the future towards {self.__class__.__name__}V2. Switch to "
            f"the usage of {self.__class__.__name__}V2 to prevent future problems.",
            DeprecationWarning,
        )

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


    @property
    def file_name(self):
        """ Make the logger filename publicly available """
        return self.__file_name

    def log(self, grid_world, agent_data):
        """ The main method to be overwritten by your own logger class.

        This method is called according to the `log_strategy` set when the logger was added the world builder. For more
        details on this see :func:`matrx.world_builder.WorldBuilder.add_logger`.

        Parameters
        ----------
        grid_world : GridWorld
            The entire grid world instance. Use this to log anything you require to log from the grid world.
        agent_data : dict
            A dictionary of all data coming from all agents' :func:`matrx.agents.agent_brain.get_log_data` methods.
            This dictionary has as keys the agent ids of all agents. As value there is the dictionary their log methods
            returned.
        Returns
        -------
        dict
            This method should return a dictionary where the keys are the columns and their value a single row. The
            keys (e.g., columns) should be always the same every consecutive call. If this is not the case an exception
            is raised.

        """
        return {}

    def _grid_world_log(self, grid_world, agent_data, last_tick=False, goal_status=None):
        """ A private MATRX method.

        This is the actual method a grid world calls for each logger. It also performs a data check on the columns and
        writes the dictionary to the file.

        Parameters
        ----------
        grid_world : GridWorld
            The grid world instance passed to the log method.
        agent_data : dict
            The agent data passed to the log method.
        last_tick : bool (default: False)
            Whether this is the last tick of the grid world or not.
        goal_status : dict
            A dictionary with all world goals (keys, WorldGoal) and whether they completed or not (value, bool)

        """
        if not self._needs_to_log(grid_world, last_tick, goal_status):
            return

        data = self.log(grid_world, agent_data)
        if data is None or data == {}:
            return

        self.__check_data(data)

        self.__write_data(data, grid_world.current_nr_ticks)

    def _needs_to_log(self, grid_world, last_tick, goal_status):
        """ A private MAtRX method.

        Checks if this logger's log method needs to be called given its log strategy.

        Parameters
        ----------
        grid_world : GridWorld
            The world instance to be logger or not.
        last_tick : bool
            Whether the world is at its last tick.
        goal_status : dict
            A dictionary with all world goals (keys, WorldGoal) and whether they completed or not (value, bool)

        Returns
        -------
        bool
            Returns True if the log method needs to be called, otherwise False.

        Raises
        ------
        Exception
            Raises a generic exception when the log strategy is not recognized as integer or of a predefined string.

        """
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
        """ A private MATRX method.

        Sets the current world number by creating a sub-folder in the save path with the given world number.

        Parameters
        ----------
        world_nr : int
            The current world number.

        """
        # Set the world number
        self.__world_nr = world_nr

        # Create the total file name path based on the world number (set by the WorldBuilder on logger creation)
        self.__save_path = f"{self.__save_path}{os.sep}world_{world_nr}"

        # Create the directory if not given
        if not os.path.exists(self.__save_path):
            os.makedirs(self.__save_path)

        self.__file_name = f"{self.__save_path}{os.sep}{self.__file_name}"

    def __check_data(self, data):
        """ A private MATRX method.

        Checks if the to be logged data uses consistent columns (e.g., if the keys of the data dict are the same as the
        one given the very first time data was logged).

        Parameters
        ----------
        data : dict
            The data to be logged from the log method.

        Returns
        -------
        bool
            Returns True if the columns are consistent with the very first time data was logged or when this is the
            first time data is being logged. False otherwise.

        Raises
        ------
        Exception
            Raises two potential exceptions: When the columns are not consistent, or when the data is not a dictionary.

        """
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
        """ A private MATRX method.

        Writes the data to the correct file.

        Parameters
        ----------
        data : dict
            The data to be logged from the log method.
        tick_nr : int
            The tick number which is being logged.

        """

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


class GridWorldLoggerV2:
    """ A class to log data during a running world.

    Loggers are meant to collect, process and write data to files during a running world. They can be added through
    the :func:`matrx.world_builder.WorldBuilder.add_logger` method. We refer to that method on how to add a logger
    to your world.

    Note that a world can have multiple loggers, each resulting in their own unique log file. So you have the
    option to create a single large log file with a single logger, or segment the data in some way over different
    files with multiple loggers. Another reason for more then one logger is a difference in logging strategy. For
    instance to have a logger that logs only at the start or end of the world and a logger that logs at every tick.

    Parameters
    ----------
    log_strategy : int, str (default: 1)
        When an integer, the logger is called every that many ticks. When a string, should be
        GridWorldLogger.LOG_ON_LAST_TICK, GridWorldLogger.LOG_ON_FIRST_TICK or GridWorldLogger.LOG_ON_GOAL_REACHED.
        Respectively for only logging on the last tick of the world, the first tick of the world or every time a
        goal is reached.
    save_path : str (default: "/logs")
        The default path were log files are stored. If the path does not exist, it is created. Otherwise log files
        are added to that path. If multiple worlds are ran from the same builder, the directory will contain
        sub-folders depicting the world's number (e.g., "world_1" for the first world, "world_2" for the second,
        etc.).
    file_name : str (default: "")
        The file name prefix. Every log file is always appended by the timestamp (Y-m-d_H:M:S) and the file
        extension. When an empty string, log file names will thus be only the timestamp.
    file_extension : str (default: ".csv")
        The file name extension to be used.
    delimiter : str (default: ";")
        The column delimiter to be used in the log files.

    """

    """Log strategy to log on the last tick of a world."""
    LOG_ON_LAST_TICK = "log_last_tick"

    """Log strategy to log on the first tick of a world."""
    LOG_ON_FIRST_TICK = "log_first_tick"

    """Log strategy to log every time a goal is reached or completed."""
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

    @property
    def file_name(self):
        """ The file name the loggers writes data to. """
        return self.__file_name

    def log(self, world_state, agent_data, grid_world):
        """ The main method to be overwritten by your own logger class.

        This method is called according to the `log_strategy` set when the logger was added the world builder. For more
        details on this see :func:`matrx.world_builder.WorldBuilder.add_logger`.

        Parameters
        ----------
        world_state : State
            The entire world state as a `State` object. Use this to quickly find and locate data you want to log.
        agent_data : dict
            A dictionary of all data coming from all agents' :func:`matrx.agents.agent_brain.get_log_data` methods.
            This dictionary has as keys the agent ids of all agents. As value there is the dictionary their log methods
            returned.
        grid_world : GridWorld
            The entire grid world instance. Use this to log anything not included into the state, such as the messages
            send between agents.
        Returns
        -------
        dict
            This method should return a dictionary where the keys are the columns and their value a single row. The
            keys (e.g., columns) should be always the same every consecutive call. If this is not the case an exception
            is raised.

        """
        return {}

    def _grid_world_log(self, world_state, agent_data, grid_world, last_tick=False, goal_status=None):
        """ A private MATRX method.

        This is the actual method a grid world calls for each logger. It also performs a data check on the columns and
        writes the dictionary to the file.

        Parameters
        ----------
        world_state : State
            The entire world state as a `State` object.
        agent_data : dict
            The agent data passed to the log method.
        grid_world: GridWorld
            The current grid world instance.
        last_tick : bool (default: False)
            Whether this is the last tick of the grid world or not.
        goal_status : dict
            A dictionary with all world goals (keys, WorldGoal) and whether they completed or not (value, bool)

        """
        if not self._needs_to_log(grid_world, last_tick, goal_status):
            return

        data = self.log(world_state, agent_data, grid_world)
        if data is None or data == {}:
            return

        self.__check_data(data)

        self.__write_data(data, grid_world.current_nr_ticks)

    def _needs_to_log(self, grid_world, last_tick, goal_status):
        """ A private MAtRX method.

        Checks if this logger's log method needs to be called given its log strategy.

        Parameters
        ----------
        grid_world : GridWorld
            The world instance to be logger or not.
        last_tick : bool
            Whether the world is at its last tick.
        goal_status : dict
            A dictionary with all world goals (keys, WorldGoal) and whether they completed or not (value, bool)

        Returns
        -------
        bool
            Returns True if the log method needs to be called, otherwise False.

        Raises
        ------
        Exception
            Raises a generic exception when the log strategy is not recognized as integer or of a predefined string.

        """
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
        """ A private MATRX method.

        Sets the current world number by creating a sub-folder in the save path with the given world number.

        Parameters
        ----------
        world_nr : int
            The current world number.

        """
        # Set the world number
        self.__world_nr = world_nr

        # Create the total file name path based on the world number (set by the WorldBuilder on logger creation)
        self.__save_path = f"{self.__save_path}{os.sep}world_{world_nr}"

        # Create the directory if not given
        if not os.path.exists(self.__save_path):
            os.makedirs(self.__save_path)

        self.__file_name = f"{self.__save_path}{os.sep}{self.__file_name}"

    def __check_data(self, data):
        """ A private MATRX method.

        Checks if the to be logged data uses consistent columns (e.g., if the keys of the data dict are the same as the
        one given the very first time data was logged).

        Parameters
        ----------
        data : dict
            The data to be logged from the log method.

        Returns
        -------
        bool
            Returns True if the columns are consistent with the very first time data was logged or when this is the
            first time data is being logged. False otherwise.

        Raises
        ------
        Exception
            Raises two potential exceptions: When the columns are not consistent, or when the data is not a dictionary.

        """
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
        """ A private MATRX method.

        Writes the data to the correct file.

        Parameters
        ----------
        data : dict
            The data to be logged from the log method.
        tick_nr : int
            The tick number which is being logged.

        """

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
