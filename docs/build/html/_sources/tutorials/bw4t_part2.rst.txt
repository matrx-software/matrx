.. _Part 2: BW4T action plan


Part 2: BW4T action plan
==========================
In deciding what action to perform, the agent loops through a list of actions that are needed to complete the task.
During the execution of these actions, the agent also keeps track of what other agents might be doing, so that the same
task will not be executed twice. Most actions need corresponding objects in the grid world in order to correctly be
executed. In the code block below, an example is given of how to save the objects for later use.

.. code-block:: python

     def decide_on_action(self, state):

        # Determine current goal for this agent
        global cycle
        self.current_goal = self.goal_cycle[0]

        # Determine which block color is needed
        if len(self.block_orders) > 0:
            current_order = self.block_orders[0]
        else:
            return StandStill.__name__, {}

        # Gather the id of this agent and the other
        this_agent = self.agent_id
        for k, obj in state.items():
            if 'Bot' in k and this_agent not in k:
                other_agent = k

        # From all objects, gather the objects that are doors and save them. This approach can be taken for every
        # object that is not a door, too!
        objects = list(state.keys())
        doors = [obj for obj in objects
                 if 'class_inheritance' in state[obj] and state[obj]['class_inheritance'][0] == "Door"]
        door_locations = []
        door_ids = []
        for door in doors:
            door_ids.append(door)
            door_location = state[door]['location']
            door_locations.append(door_location)

        return StandStill.__name__, {}
For every action an agent should perform, a separate case in the action decision plan needs to be defined. The implementation
of the first action, finding the correct room, is explained below. It should be added to 'decide_on_action' that is
described above. The other actions follow similar steps. They can be added according to your liking.

.. code-block:: python

        # First, check if the other agent(s) have sent messages. (See GitHub for method implementation)
        self.check_for_update(current_order)

        # Navigate to a room
        if self.current_goal == "find_room":
            self.navigator.reset_full()
            # Setting location that is in front of a door
            for doormat in doormats:
                doormat_id = doormats[doormat]['doormat_id']
                if current_order in doormat_id:
                    doormat_waypoint = doormats[doormat]['location']
                    self.navigator.add_waypoint(doormat_waypoint)
                    move_action = self.navigator.get_move_action(self.state_tracker)

                    current_waypoint = doormat_waypoint
                    # Update other agent(s) that this order is already executed
                    if self.agent_properties['location'] == current_waypoint:
                        self.send_message(message_content={"id": doormat_id},
                                          to_id=other_agent)
                        self.goal_cycle.pop(0)

            # Return the action from the Navigator
            return move_action, {}
For the full code example, including the other action states, see the MATRXS GitHub page.