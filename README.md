# Testbed

2D-discrete testbed to facilitate HAT-research, with SAIL connection

For documentation see the wiki at [https://ci.tno.nl/gitlab/SAIL-framework/testbed/wikis/home](https://ci.tno.nl/gitlab/SAIL-framework/testbed/wikis/home).

# Changes
- run_sail_api -> run_matrxs_api
- maybe check navigator -> traversable objs (smoke) overwrote intravers objs (wall). Agent got stuck in infinite try walk through wall loop.



# Todo:
- create extra loop which catches reset and fully stops and resets visualizer. Send world ID along which is checked, 
and vis reset if different?
- port API to worldbuilder level
- check transition to next experiment
- Jasper: property maken van global variable -> issue. 
- message(with from and to_id) as message content?