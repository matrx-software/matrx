# Testbed

2D-discrete testbed to facilitate HAT-research, with SAIL connection

For documentation see the wiki at [https://ci.tno.nl/gitlab/SAIL-framework/testbed/wikis/home](https://ci.tno.nl/gitlab/SAIL-framework/testbed/wikis/home).

# Changes
- run_sail_api -> run_matrxs_api
- maybe check navigator -> traversable objs (smoke) overwrote intravers objs (wall). Agent got stuck in infinite try walk through wall loop.



# Todo:
- fix smooth movement
- fix agent / human views
- fix userinput
- fix bg colour
- fix bg img
- issue: how to make settings available via the API (e.g. bg_img), such that users / agents can edit it, and users / agents can also add extra info.
- function 
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
Advantage is that agents can change it (using actions) and also read it. 
Settings are also passed automatically via the API, which is required for the visualization. 
