# Testbed

2D-discrete testbed to facilitate HAT-research, with SAIL connection


# animated movement notes
- prev_location property of agents needs to be available to other agents
- users might want to control if movements are animated (teleport vs normal movement?)

Solutions:   
- add prev_location as official agent property which is not editable by users
- do an extra loop over all agents to fetch all prev_locations, and save it in the state of all agents
- save objects copy with prev_locations in visualizers
- save objects with prev_locations in GUI

Other todos:
- fix for human agents as well 
