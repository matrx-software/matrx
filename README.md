# Testbed

2D-discrete testbed to facilitate HAT-research, with SAIL connection

For documentation see the wiki at [https://ci.tno.nl/gitlab/SAIL-framework/testbed/wikis/home](https://ci.tno.nl/gitlab/SAIL-framework/testbed/wikis/home).

# Changes
- run_sail_api -> run_matrxs_api
- maybe check navigator -> traversable objs (smoke) overwrote intravers objs (wall). Agent got stuck in infinite try walk through wall loop.



# Todo:
- subspecify API messages:
    - send message 
- agents should also be able to received data. Are there other types of input except from userinput0? Why should there be a difference between human and normal agents? 
Advantage is that agents can change it (using actions) and also read it. API input?
Settings are also passed automatically via the API, which is required for the visualization. 
- Jasper: property maken van global variable -> issue. 


message: 
- from current (human) agent  
- to self / other agent 
- content 