.. _Logging:

======
Logging
======

The MATRX simulation can be logged every tick, with results written to csv files. By default a number of loggers are
already implemented and ready to use:


.. autosummary::
   :toctree: _generated_autodoc

    matrx.logger.log_agent_actions.LogActions
    matrx.logger.log_idle_agents.LogIdleAgents
    matrx.logger.log_tick.LogDuration
    matrx.logger.logger.GridWorldLogger
