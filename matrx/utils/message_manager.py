from matrx.agents.agent_brain import  Message

class MessageManager():
    """ A manager inside the GirdWorld that tracks the received and send messages between agents and their teams.

        This gives provides several advantages;
        - an easier connection between Core, API and Front-end for messages (e.g. to differentiate between messages send between agents and to teams in the Front-end through a simple API call: 'get_team_messages').
        - an easy way to log communication (as the messages are easily obtained from a GridWorld instance, through some methods).
    """

    def __init__(self):
        # there are three types of messages
        self.global_messages = {} # messages send to everyone
        self.team_messages = {} # messages send to a team
        self.private_messages = {} # messages send to individual agents

        self.preprocessed_messages = {} # all types of messages above unpacked to the corresponding individual messages

        self.agents = None
        self.teams = None
        self.current_available_tick = 0

    def preprocess_messages(self, tick, messages, all_agent_ids, teams):
        """ Preprocess messages for sending, such that they can be understood by the GridWorld.
            For example: if the receiver=None, this means it must be sent to all agents. This function creates a message
            directed at every agent.

            Parameters
            ----------
            tick
                Current tick of the gridworld
            messages
                All messages sent from the agent brains in the gridworld, and received via the API
            all_agent_ids
                IDs of all the agents


            Returns
                Preprocessed messages ready for sending
            -------
            """
        self.teams = teams
        self.agents = all_agent_ids

        # process every message
        for mssg in messages:

            # initialize a list for messages for this tick
            if not tick in self.preprocessed_messages:
                self.preprocessed_messages[tick] = []

            # check the message for validity
            MessageManager.__check_message(mssg, mssg.from_id)

            # decode the receiver_string into agent / team / global messages, save seperatly, and split into individual
            # messages understandable by the GridWorld
            self._decode_message_receiver(mssg, all_agent_ids, teams, tick)


    def _decode_message_receiver(self, mssg, all_agent_ids, teams, tick):
        """ Processes messages directed at other agents / teams / everyone.

        These types are called private, team, and global messages.
        Messages of each type are saved for every tick seperatly, as well as a list with all preprocessed messages
        suitable for sending by the GridWorld.

        Possible formats for mssg.to_id
        "agent1"                  = private message to agent1 + team "agent1" if it exists
        ["agent1", "agent2"]      = 2 private messages + team messages if likewise named teams exist
        "team2"                   = team message sent to everyone in that team
        '["agent3", "team4"]'     = team + agent message. Provided as a string via the API
        None                      = global message send to everyone

        Parameters
        ----------
        mssg
            The original mssg object sent by the agent, or received via the API

        all_agent_ids
            List with IDs of all agents

        teams
            Dict with all team names (keys), and a list with all agent IDs in that team (value)

        tick
            Current tick of the gridworld
        """
        all_ids_except_me = [agent_id for agent_id in all_agent_ids if agent_id != mssg.from_id]

        # if the receiver is None, it is a global message which has to be sent to everyone
        if mssg.to_id is None: # global message
            # create a list in memory for global messages for this tick
            if tick not in self.global_messages:
                self.global_messages[tick] = []

            # save in global
            global_message = Message(content=mssg.content, from_id=mssg.from_id, to_id="global")
            self.global_messages[tick].append(global_message)

            # split in sub mssgs
            for to_id in all_ids_except_me.copy():
                # create message
                new_message = Message(content=mssg.content, from_id=mssg.from_id, to_id=to_id)

                # save in prepr
                self.preprocessed_messages[tick].append(new_message)  # all messages above combined

        # if it is a list, decode every receiver_id in that list again
        elif isinstance(mssg.to_id, list):
            for receiver_id in mssg.to_id:
                # create message
                new_message = Message(content=mssg.content, from_id=mssg.from_id, to_id=receiver_id)

                self._decode_message_receiver(new_message, all_agent_ids, teams, tick)

        # a string might be: a list encoded as a string, a team, or an agent_id.
        elif isinstance(mssg.to_id, str):
            is_team_message = False

            try:
                # check if it is a list encoded as a string (sent via API)
                to_ids = eval(mssg.to_id)

                # create a new message addressed to this list of IDs, and reprocess
                new_message = Message(content=mssg.content, from_id=mssg.from_id, to_id=to_ids)
                self._decode_message_receiver(new_message, all_agent_ids, teams, tick)
            except:
                pass

            # Check if mssg_to is a teamname. Note: an agent can only send a message to a team if they are in it.
            if mssg.to_id in teams.keys() and mssg.from_id in teams[mssg.to_id]:
                # create a list in memory for this team for this tick
                if tick not in self.team_messages:
                    self.team_messages[tick] = {}
                if mssg.to_id not in self.team_messages[tick]:
                    self.team_messages[tick][mssg.to_id] = []

                is_team_message = True

                # save in team mssgs as a message for that specific team
                self.team_messages[tick][mssg.to_id].append(mssg)


                # split in sub mssgs for every agent in the team
                for to_id in teams[mssg.to_id]:
                    # create a message
                    new_message = Message(content=mssg.content, from_id=mssg.from_id, to_id=to_id)

                    # save in prepr
                    self.preprocessed_messages[tick].append(new_message)

            # check if it is an agent ID (as well)
            # If no team is set by the user, the agent is added to a new team with the same name as the agent's ID.
            # As such, a message can be targeted at a team and individual agent at the same time.
            if mssg.to_id in all_agent_ids:
                # create a list in memory for private messages for this tick
                if tick not in self.private_messages:
                    self.private_messages[tick] = []

                # save in private_messages mssgs
                self.private_messages[tick].append(mssg)

                # if the message was not already saved in the preprocessed list, save it there as well
                if not is_team_message:
                    self.preprocessed_messages[tick].append(mssg)


    @staticmethod
    def __check_message(mssg, this_agent_id):
        if not isinstance(mssg, Message):
            raise Exception(f"A message to {this_agent_id} is not, nor inherits from, the class {Message.__name__}."
                            f" This is required for agents to be able to send and receive them.")


    def fetch_chatrooms(self, id=None):
        """ Fetch all the chatrooms which an agent can view (or all if no ID provided)

        Parameters
        ----------
        id
            ID of the agent for which to fetch all accessible chatrooms

        Returns
        -------
            A dictionary containing a list with all "private" chatrooms, all "teams" chatrooms, and a "global" key,
            accessible via likewise named keys.
        """

        chatrooms = {"private": [], "team": [], "global": None}

        # add agents with which can be conversed
        for agent_id in self.agents:
            if agent_id != id:
                chatrooms['private'].append(agent_id)

        # add teams with which can be conversed
        for team_name, team_members in self.teams.items():
            # if a specific agent ID is provided, only add teams of which that agent is a member
            if id != None:
                if id in team_members or id == "god":
                    chatrooms['team'].append(team_name)
            # otherwise, all teams can be conversed with
            else:
                chatrooms['team'].append(team_name)

        return chatrooms



    def fetch_messages(self, tick_from, tick_to, id=None):
        """ Fetch messages, optionally filtered by start tick and/or agent id.

        Parameters
        ----------
        tick_from
            All messages from `tick_from` onwards to (including) `tick_to` will be collected.
        tick_to
            All messages from `tick_from` onwards to (including) `tick_to` will be collected.
        id
            Only messages received by or sent by this agent will be collected.

        Returns
        -------
        Dictionary containing a 'global', 'team', and 'private' subdictionary.
        Global messages: messages['global'][tick] = [list of messages]
        Team messages: messages['team'][tick][team] = [list of messages]
        Private messages: messages['private'][tick] = [list of messages]

        """
        messages = {'global': {}, 'team': {}, 'private': {}}

        # loop through all requested ticks
        for t in range(tick_from, tick_to + 1):
            # initialize the message objects to return
            # messages['global'][t] = None
            # messages['team'][t] = None
            # messages['private'][t] = None

            # fetch any existing glolbal messages for this tick
            if t in self.global_messages:
                # make the messages JSON serializable and add
                messages['global'][t] = [mssg.toJSON() for mssg in self.global_messages[t]]

            # fetch any team messages
            if t in self.team_messages:
                if t not in messages['team']:
                    messages['team'][t] = {}

                # fetch all team messages
                if id is None:
                    # make them JSON serializable
                    messages['team'][t] = [mssg.toJSON() for mssg in self.team_messages[t]]

                # fetch team messages of the team of which the agent is a member
                else:
                    for team in self.teams:
                        if (id in team or id == "god") and team in self.team_messages[t]:
                            # make the messages JSON serializable and add
                            messages['team'][t][team] = [mssg.toJSON() for mssg in self.team_messages[t][team]]


            # fetch private messages
            if t in self.private_messages:
                # fetch all private messages
                if id is None:
                    # make the messages JSON serializable and add
                    messages['private'][t] = [mssg.toJSON() for mssg in self.private_messages[t]]

                # fetch private messages sent to or received by the specified agent
                else:
                    messages['private'][t] = []
                    for message in self.private_messages[t]:
                        # only private messages addressed to or sent by our agent are requested
                        if message.from_id == id or message.to_id == id or id == "god":
                            # make the messages JSON serializable and add
                            messages['private'][t].append(message.toJSON())

        return messages
