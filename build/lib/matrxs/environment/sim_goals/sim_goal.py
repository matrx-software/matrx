import numpy as np


class SimulationGoal:
    """
    A class that tracks whether the simulation has reached its global goal.
    """

    def __init__(self):
        """
        We set the self.is_done to False as a start.
        """
        self.is_done = False

    def goal_reached(self, grid_world):
        """
        Returns whether the global goal of the simulated grid world is accomplished. This method should be overridden
        by a new goal function.
        :param grid_world: An up to date representation of the grid world that will be analyzed in this function on
        whether a specific coded global goal is reached.
        :return: True when the goal is reached, False otherwise.
        """
        pass

    def get_progress(self, grid_world):
        """
        Returns the progress of reaching the global goal in the simulated grid world. This method can be overridden
        if you want to track the progress. But is not required.
        :param grid_world: An up to date representation of the grid world that will be analyzed in this function on
        how far we are in obtaining the global simulation goal.
        :return: A Float representing with 0.0 no progress made, and 1.0 that the goal is reached.
        """
        pass


class LimitedTimeGoal(SimulationGoal):
    """
    A simulation goal that simply tracks whether a maximum number of ticks has been reached.
    """

    def __init__(self, max_nr_ticks):
        super().__init__()
        self.max_nr_ticks = max_nr_ticks

    def goal_reached(self, grid_world):
        nr_ticks = grid_world.current_nr_ticks
        if self.max_nr_ticks == np.inf or self.max_nr_ticks <= 0:
            self.is_done = False
        else:
            if nr_ticks >= self.max_nr_ticks:
                self.is_done = True
            else:
                self.is_done = False
        return self.is_done

    def get_progress(self, grid_world):
        if self.max_nr_ticks == np.inf or self.max_nr_ticks <= 0:
            return 0.
        return min(1.0, grid_world.current_nr_ticks / self.max_nr_ticks)
