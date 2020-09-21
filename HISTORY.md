V1.0 (25/03/2020)
=================
The first official release of MATRX.

Features
---------

- The MATRX Core. This functions as a (grid-based) finite state machine to model the effects of a set of actions decided upon by a equally sized set of agents on a current world state in such a way that these effects lead to a new world state. The Core includes the following:
  - The Game Loop: The continuous loop between discrete world states in which, among others, agents are queried for actions and these actions are applied.
  - The World: The container of the (often gird-based) finite state machine.
  - The World Builder: This allows for the creation of new new tasks, by offering numerous helper functions to quickly do so.
  - The Environment Object: Everything in a MATRX world is an object, and the Environment Object describes the information that makes up an object.
  - The Agent Body and Agent Brain: Agents in MATRX are seperated in body and mind. The Body is the object representation of an agent in the world. The Brain contains all the decision logic for an agent.
  - The Human Agent: An interface that allows a human to control an agent in a spatial grid-based environment.

- The MATRX API. This is the connection between the MATRX Core and potential outside packages. For example, a visualisation of a world state or agent behavior, but also potential 2nd and 3rd party software.

- The MATRX Visualisation. This is the basic visualisation of a MATRX world. This assumes that the task is spatial and grid-based.

Dissemination
--------------

- The MATRX websites.
  - The main website: A central point providing general information about MATRX for users, developers and maintainers of MATRX. www.matrx-software.com
  - The documentation website: The pages that contain an extensive documentation of all private and public code of MATRX. http://docs.matrx-software.com/en/latest/

- The Logo and Style. A singular style for MATRX, including a multi-purpose logo.
