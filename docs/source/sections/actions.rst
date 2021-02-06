.. _Actions:

=============
Actions
=============

Agents can change (or mutate) the world through performing actions. When an
agent decides on an action it will communicate the action name and potential
arguments to the world. The world then checks if the action is indeed possible,
and performs that action if so.

.. autosummary::
    :nosignatures:
    :toctree: _generated_autodoc

    matrx.actions.action.Action

--------------
Object Actions
--------------

These are all the actions mutating objects in the world.

.. autosummary::
    :nosignatures:
    :toctree: _generated_autodoc

    matrx.actions.object_actions.RemoveObject
    matrx.actions.object_actions.GrabObject
    matrx.actions.object_actions.DropObject
    matrx.actions.door_actions.OpenDoorAction
    matrx.actions.door_actions.CloseDoorAction


------------
Move Actions
------------

These are all the actions for moving the agent from one location to another.

.. autosummary::
    :nosignatures:
    :toctree: _generated_autodoc

    matrx.actions.move_actions.Move
    matrx.actions.move_actions.MoveNorth
    matrx.actions.move_actions.MoveNorthEast
    matrx.actions.move_actions.MoveEast
    matrx.actions.move_actions.MoveSouthEast
    matrx.actions.move_actions.MoveSouth
    matrx.actions.move_actions.MoveSouthWest
    matrx.actions.move_actions.MoveWest
    matrx.actions.move_actions.MoveNorthWest

==============
Action results
==============

The world communicates back to agents how their actions went. This information
is wrapped in so-called 'action results'. Simple wrappers around some data
denoting if an action succeeded or not, and the potential reasons for it.

.. autosummary::
    :nosignatures:
    :toctree: _generated_autodoc

    matrx.actions.action.ActionResult
    matrx.actions.object_actions.RemoveObjectResult
    matrx.actions.object_actions.GrabObjectResult
    matrx.actions.object_actions.DropObjectResult
    matrx.actions.door_actions.OpenDoorActionResult
    matrx.actions.door_actions.CloseDoorActionResult
    matrx.actions.move_actions.MoveActionResult