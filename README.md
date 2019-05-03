# Testbed

2D-discrete testbed to facilitate HAT-research, with SAIL connection


# animated movement notes

Solution:
For animating smooth movement of objects, the visualizer keeps track of object IDs (which move) and their location, such that
it can animate movement from a previous location to the new passed location.

Additions:
- add `animate_movement` property to objects and agents which can be toggled by user.
