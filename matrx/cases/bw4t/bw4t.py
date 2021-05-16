import itertools
from collections import OrderedDict
from itertools import product

from matrx import WorldBuilder, utils
import numpy as np
from matrx.actions import MoveNorth, OpenDoorAction, CloseDoorAction
from matrx.actions.move_actions import MoveEast, MoveSouth, MoveWest
from matrx.agents import AgentBrain, HumanAgentBrain, SenseCapability
from matrx.cases.bw4t.bw4t_agents import BlockWorldAgent
from matrx.cases.bw4t.bw4t_objects import CollectBlock, SignalBlock
from matrx.grid_world import GridWorld, DropObject, GrabObject, AgentBody
from matrx.objects import EnvObject, SquareBlock
from matrx.world_builder import RandomProperty
from matrx.goals import WorldGoal, CollectionGoal

# Some general settings
tick_duration = 1 / 60  # 60fps if achievable
random_seed = 1
verbose = False
key_action_map = {  # For the human agents
    'w': MoveNorth.__name__,
    'd': MoveEast.__name__,
    's': MoveSouth.__name__,
    'a': MoveWest.__name__,
    'q': GrabObject.__name__,
    'e': DropObject.__name__,
    'r': OpenDoorAction.__name__,
    'f': CloseDoorAction.__name__,
}


def get_room_loc(room_nr):
    row = np.floor(room_nr / 3)
    column = room_nr % 3

    # x is: +1 for the edge, +edge hallway, +room width * column nr
    room_x = int(1 + 3 + (7 * column))

    # y is: +1 for the edge, +hallway space * (nr row + 1 for the top hallway), +row * room height
    room_y = int(1 + 3 * (row + 1) + row * 7)

    # door location is always center top
    door_x = room_x + int(np.floor(7 / 2))
    door_y = room_y

    return (room_x, room_y), (door_x, door_y)


def add_blocks(builder, room_locations, block_colours):
    for room_name, locations in room_locations.items():
        for loc in locations:
            # Get the block's name
            name = f"Block in {room_name}"

            # Get the probability for adding a block so we get the on average the requested number of blocks per room
            prob = min(1.0, 4 / len(locations))

            # Create a MATRX random property of color so each block varies per created world.
            # This random property is used to obtain a certain value (a color) for a certain object property
            # (visualize_colour) each time a new world is created from this builder.
            colour_property = RandomProperty(values=block_colours)

            # Add the block; a regular CollectibleObject as denoted by the given 'callable_class' which the
            # builder will use to create the object. In addition to setting MATRX properties, we also
            # provide a `is_block` boolean as custom property so we can identify this as a collectible
            # block.
            builder.add_object_prospect(loc, name, callable_class=CollectBlock, probability=prob,
                                        visualize_colour=colour_property)


def add_drop_off_zone(builder, world_size, block_colours, nr_blocks_to_collect):
    # First we calculate the top left coordinates of the room that contains our drop off zone
    x = 7
    y = 34
    door_x = 14
    door_y = y

    # Add the drop off room, with a door at its top
    builder.add_room(top_left_location=(x, y), width=15, height=7, name="Drop_off",
                     door_locations=[(door_x, door_y)])

    # Get all the locations INSIDE this room, again using a handy builder method.
    locs = utils.get_room_locations(room_top_left=(x, y), room_width=15, room_height=7)

    # Since we want each created world from our builder to have a different set of blocks to collect, we make a random
    # property that samples from all possible orderings of block colours (with duplicates). There is a handy class
    # method in `utils` that does this for us!
    possibilities = [{"visualization_colour": c} for c in block_colours]
    rp_order = CollectionGoal.get_random_order_property(possibilities, length=nr_blocks_to_collect,
                                               with_duplicates=True)

    # Create a collection goal. A collection goal in MATRX consists of the actual `CollectionGoal` that is linked to a
    # certain area that functions as the 'drop zone' and an invisible object containing a list of properties that
    # describe the to be collected objects. The `WorldBuilder` offers a handy method to create such goal, area and
    # invisible object. It requires the locations of this 'drop zone' and the list of properties describing the to be
    # collected objects. This list will become an actual property of our invisible object, thus it can also be a
    # RandomProperty instance! This enables us to vary the required order every time a new world is created. We just
    # made this property, so we just pass it through. We also set the colour and the opacity of the 'drop zone'.
    drop_zone_name = "Drop zone"
    builder.add_collection_goal(drop_zone_name, locs, rp_order, in_order=True,
                                collection_area_colour="#c87800",
                                collection_area_opacity=0.5, overwrite_goals=True)

    # Add our signal block that adapt itself to the then generated blocks to be collected.
    loc = (1, world_size[1] - 1 - nr_blocks_to_collect)
    for rank in range(nr_blocks_to_collect):
        builder.add_object(loc, name="Signal block", callable_class=SignalBlock, drop_zone_name=drop_zone_name,
                           rank=rank)
        loc = (loc[0], loc[1] + 1)


def add_agents(builder, block_sense_range, other_sense_range, memorize_for_ticks):
    # Create the agents sense capability. This is a circular range around the agent that denotes what it can perceive.
    # Here, we define that the agent cannot see other agent's their bodies, they can see square blocks with their own
    # range and see all other objects (doors, walls, etc.) with another range.
    sense_capability = SenseCapability({AgentBody: 0,
                                        CollectBlock: block_sense_range,
                                        None: other_sense_range})

    # Now we add our agents as part of the same team
    team_name = "Team Awesome"

    # We add 1 Human Agent; which is an agent you can control yourself. We first create the brain of the agent, and then
    # add it to our builder.
    brain = HumanAgentBrain(max_carry_objects=1, grab_range=0, drop_range=0, fov_occlusion=True,
                            memorize_for_ticks=memorize_for_ticks)
    loc = (1, 1)
    builder.add_human_agent(loc, brain, team=team_name, name="Human", key_action_map=key_action_map,
                            sense_capability=sense_capability)

    # We add 2 additional Autonomous Agents; an agent that does its thing without needing your input. Again, we create
    # its brain and add it to our builder. Since we provide the same team name, these agents will be in the same team as
    # the Human Agent.
    loc = (2, 1)
    brain = BlockWorldAgent()
    builder.add_agent(loc, brain, team=team_name, name=f"Agent Smith #1", sense_capability=sense_capability)
    loc = (3, 1)
    brain = BlockWorldAgent()
    builder.add_agent(loc, brain, team=team_name, name=f"Agent Smith #2", sense_capability=sense_capability)


def add_rooms(builder):
    room_locations = {}
    for room_nr in range(9):
        room_top_left, door_loc = get_room_loc(room_nr)

        # Add the room
        room_name = f"room_{room_nr}"
        builder.add_room(top_left_location=room_top_left, width=7, height=7, name=room_name,
                         door_locations=[door_loc], wall_visualize_colour="#8a8a8a",
                         with_area_tiles=True, area_visualize_colour="#dbdbdb", area_visualize_opacity=0.1)

        # Find all inner room locations where we allow objects (making sure that the location behind to door is free)
        room_locations[room_name] = utils.get_room_locations(room_top_left, 7, 7)

    return room_locations


def create_builder():
    # Some BW4T settings
    block_colours = ['#ff0000', '#ffffff', '#ffff00', '#0000ff', '#00ff00', '#ff00ff']
    block_sense_range = 10  # the range with which agents detect blocks
    other_sense_range = np.inf  # the range with which agents detect other objects (walls, doors, etc.)
    memorize_for_ticks = (10 / tick_duration)  # we want to memorize states for (seconds / tick_duration ticks) ticks

    # Set numpy's random generator
    np.random.seed(random_seed)

    # The world size, with plenty of space for agents to move between rooms
    world_size = (30, 44)

    # Create our world builder
    builder = WorldBuilder(shape=world_size, tick_duration=tick_duration, random_seed=random_seed, run_matrx_api=True,
                           run_matrx_visualizer=True, verbose=verbose, visualization_bg_clr="#f0f0f0",
                           visualization_bg_img="")

    # Add the world bounds (not needed, as agents cannot 'walk off' the grid, but for visual effect)
    builder.add_room(top_left_location=(0, 0), width=world_size[0], height=world_size[1], name="world_bounds")

    # Create the rooms
    room_locations = add_rooms(builder)

    # Add the blocks the agents need to collect, we do so probabilistically so each world will contain different blocks
    add_blocks(builder, room_locations, block_colours)

    # Create the drop-off zones, this includes generating the random colour/shape combinations to collect.
    add_drop_off_zone(builder, world_size, block_colours, nr_blocks_to_collect=2)

    # Add the agents and human agents to the top row of the world
    add_agents(builder, block_sense_range, other_sense_range, memorize_for_ticks)

    # Return the builder
    return builder


def run(nr_of_worlds=1):
    # Create our world builder
    builder = create_builder()

    # Start overarching MATRX scripts and threads, such as the api and/or visualizer if requested. Here we also link our
    # own media resource folder with MATRX.
    # media_folder = os.path.join(os.path.dirname(__file__), "media")
    builder.startup()

    for world in builder.worlds(nr_of_worlds=nr_of_worlds):
        world.run(builder.api_info)

    builder.stop()
