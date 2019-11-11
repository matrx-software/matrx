# Testbed

2D-discrete testbed to facilitate HAT-research, with SAIL connection

For documentation see the wiki at [https://ci.tno.nl/gitlab/SAIL-framework/testbed/wikis/home](https://ci.tno.nl/gitlab/SAIL-framework/testbed/wikis/home).

# Changes
- run_sail_api -> run_matrxs_api
- maybe check navigator -> traversable objs (smoke) overwrote intravers objs (wall). Agent got stuck in infinite try walk through wall loop.



# Todo:
- check userinput
- fix bg colour
- fix bg img
- extend World object to: 
```
state["World"] = {
    "nr_ticks": self.__current_nr_ticks,
    "grid_shape": self.__shape,
    "vis_settings": { 
        "visualization_bg_clr": self.visualization_bg_clr,
        "visualization_bg_img": self.visualization_bg_img    
    }
} 
```
- Jasper: property maken van global variable -> issue. 
Advantage is that agents can change it (using actions) and also read it. 
Settings are also passed automatically via the API, which is required for the visualization. 
