.. _Implementing an agent brain

===========================
Implementing an agent brain
===========================

Agent brains in MATRXS are used to give meaning to the actions an agent takes in the environment. By implementing an
agent brain, the logic and decision processes of the agent are determined. You can decide what action the agent will take
given a certain situation by creating a new behavior class based on the AgentBrain class.

The most important methods for users that want to create a variation on an AgentBrain are *initialize*,
*filter_observations*, and *decide_on_action*. The initialization of the brain is needed as this is what connects the
agent's behavior to the grid world. The agent is, most likely, not an all-knowing being, so by filtering some objects/agents
from the environment, a more realistic representation of the world as is known to the agent can be created. For example,
when a door to a room is closed, the agent probably is not able to know what is inside the room unless the door was open
before. In this case, everything behind a door that has never been opened before should be filtered out of the state.
Lastly, every action that the agents takes is determined in *decide_on_action*. Depending on the context, this method returns
an action (moving, picking up, etc.) for every situation the agent can find itself in.

For examples of how to implement a new agent brain, you can take a look at the tutorials about :ref:`BW4T<Part 1: BW4T skeleton>`. Here, all assets of
creating an agent's brain are implemented and examples are shown.


