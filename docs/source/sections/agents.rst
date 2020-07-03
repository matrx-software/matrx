.. _Agents:

======
Agents
======

To implement the desired behaviour of agents, the classes below can be used. Usually, human agents are controlled by
user input, while the autonomous system uses a brain implemented by the user via its own class. See the tutorials on how
to implement an agent brain to know how.


------------
Base classes
------------

These are the most basic agents.

.. autosummary::
   :toctree: _generated_autodoc

   matrx.agents.agent_brain.AgentBrain
   matrx.agents.agent_types.human_agent.HumanAgentBrain


---------------
Specific agents
---------------

These are agents that show some more complex behavior.

.. autosummary::
   :toctree: _generated_autodoc

   matrx.agents.agent_types.patrolling_agent.PatrollingAgentBrain


------------------
Agent capabilities
------------------

What an agent can do, is specified with capabilities. Currently, MATRX only
supports a sensing capability which is used to construct the world's state as
perceived by the agent.

.. autosummary::
   :toctree: _generated_autodoc

   matrx.agents.capabilities.capability.Capability
   matrx.agents.capabilities.capability.SenseCapability

------------------
Agent utils
------------------

These are utilities functions that help ease the development of agents, or creating more advanced agent behaviour.

.. autosummary::
   :toctree: _generated_autodoc

   matrx.agents.agent_utils.fov
   matrx.agents.agent_utils.navigator.Navigator
   matrx.agents.agent_utils.state_tracker.StateTracker
   matrx.agents.agent_utils.task_manager.TaskManager
