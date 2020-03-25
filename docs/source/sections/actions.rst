.. _Actions:

=======
Actions
=======

Agents can change (or mutate) the world through performing actions. When an
agent decides on an action it will communicate the action name and potential
arguments to the world. The world then checks if the action is indeed possible,
and performs that action if so.

.. autosummary::
    :nosignatures:
    :toctree: _generated_autodoc

    matrxs.actions.action.Action

--------------
Object Actions
--------------

These are all the actions mutating objects in the world.

.. autosummary::
    :nosignatures:
    :toctree: _generated_autodoc

    matrxs.actions.object_actions.RemoveObject
    matrxs.actions.object_actions.GrabObject
    matrxs.actions.object_actions.DropObject
    matrxs.actions.door_actions.OpenDoorAction
    matrxs.actions.door_actions.CloseDoorAction


------------
Move Actions
------------

These are all the actions for moving the agent from one location to another.

.. autosummary::
    :nosignatures:
    :toctree: _generated_autodoc

    matrxs.actions.move_actions.Move
    matrxs.actions.move_actions.MoveNorth
    matrxs.actions.move_actions.MoveNorthEast
    matrxs.actions.move_actions.MoveEast
    matrxs.actions.move_actions.MoveSouthEast
    matrxs.actions.move_actions.MoveSouth
    matrxs.actions.move_actions.MoveSouthWest
    matrxs.actions.move_actions.MoveWest
    matrxs.actions.move_actions.MoveNorthWest

==============
Action results
==============

The world communicates back to agents how their actions went. This information
is wrapped in so-called 'action results'. Simple wrappers around some data
denoting if an action succeeded or not, and the potential reasons for it.

.. autosummary::
    :nosignatures:
    :toctree: _generated_autodoc

    matrxs.actions.action.ActionResult
    matrxs.actions.object_actions.RemoveObjectResult
    matrxs.actions.object_actions.GrabObjectResult
    matrxs.actions.object_actions.DropObjectResult
    matrxs.actions.door_actions.OpenDoorActionResult
    matrxs.actions.door_actions.CloseDoorActionResult
    matrxs.actions.move_actions.MoveActionResult