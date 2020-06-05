import numpy as np


class WorldGoal:
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

        Parameters
        ----------
        grid_world : GridWorld
            An up to date representation of the grid world that will be analyzed in this function on
            whether a specific coded global goal is reached.

        Returns
        -------
        goal_reached : bool
            True when the goal is reached, False otherwise.
        """
        pass

    def get_progress(self, grid_world):
        """
        Returns the progress of reaching the global goal in the simulated grid world. This method can be overridden
        if you want to track the progress. But is not required.

        Parameters
        ----------
        grid_world : GridWorld
            An up to date representation of the grid world that will be analyzed in this function on
            how far we are in obtaining the global world goal.

        Returns
        -------
        progress : float
            Representing with 0.0 no progress made, and 1.0 that the goal is reached.
        """
        pass


class LimitedTimeGoal(WorldGoal):
    """
    A world goal that simply tracks whether a maximum number of ticks has been reached.
    """

    def __init__(self, max_nr_ticks):
        """ Initialize the LimitedTimeGoal by saving the `max_nr_ticks`.
        """
        super().__init__()
        self.max_nr_ticks = max_nr_ticks

    def goal_reached(self, grid_world):
        """ Returns whether the number of specified ticks has been reached.

        Parameters
        ----------
        grid_world : GridWorld
            An up to date representation of the grid world that will be analyzed in this function on
            whether a specific coded global goal is reached.

        Returns
        -------
        goal_reached : bool
            True when the goal is reached, False otherwise.

        Examples
        --------

        For an example, see :meth:`matrx.grid_world.__check_simulation_goal`

        Checking all simulation goals from e.g. action, world goal, or somewhere else with access to the Gridworld,
        the function can be used as below:

        >>> goal_status = {}
        >>> if grid_world.simulation_goal is not None:
        >>>     if isinstance(grid_world.simulation_goal, list):
        >>>         for sim_goal in grid_world.simulation_goal:
        >>>             is_done = sim_goal.goal_reached(grid_world)
        >>>             goal_status[sim_goal] = is_done
        >>>     else:
        >>>         is_done = grid_world.simulation_goal.goal_reached(grid_world)
        >>>         goal_status[grid_world.simulation_goal] = is_done
        >>>
        >>> is_done = np.array(list(goal_status.values())).all()

        """
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
        """ Returns the progress of reaching the LimitedTimeGoal in the simulated grid world.

        Parameters
        ----------
        grid_world : GridWorld
            An up to date representation of the grid world that will be analyzed in this function on
            how far we are in obtaining the global world goal.

        Returns
        -------
        progress : float
            Representing with 0.0 no progress made, and 1.0 that the goal is reached.


        Examples
        --------
        Checking all simulation goals from e.g. action, world goal, or somewhere else with access to the Gridworld,
        the function can be used as below.
        In this example we know there is only 1 simulation goal.

        >>> progress = grid_world.simulation_goal.get_progress(grid_world)
        >>> print(f"The simulation is {progress * 100} percent complete!")


        """
        if self.max_nr_ticks == np.inf or self.max_nr_ticks <= 0:
            return 0.
        return min(1.0, grid_world.current_nr_ticks / self.max_nr_ticks)
