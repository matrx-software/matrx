import copy

from matrx.messages.message import Message
from itertools import combinations

class MessageManager:
    """ A manager inside the GirdWorld that tracks the received and send messages between agents and their teams.

        This provides several advantages:
        - an easier connection between MATRX Core, MATRX API, and the Front-end for
        messages (e.g. to differentiate between messages send between agents and to teams in the Front-end through a
        simple api call: 'get_team_messages').
        - an easy way to log communication (as the messages are easily obtained from a GridWorld instance, through some
        methods).
    """

    def __init__(self):
        # contains all chatrooms and their messages
        self.chatrooms = []

        # add the global chatroom
        global_chatroom = Chatroom(ID=len(self.chatrooms), name="Global", type="global")
        self.chatrooms.append(global_chatroom)
        # check if we have initialized the chatrooms during the first tick of the simulation
        self.initialized_chatrooms = False

        # contains all messages unpacked to the corresponding individual messages
        self.preprocessed_messages = {}

        self.agents = None
        self.teams = None
        self.current_available_tick = 0

        self.message_id = 0

    def preprocess_messages(self, tick, messages, all_agent_ids, teams):
        """ Preprocess messages for sending, such that they can be understood by the GridWorld.

        For example: if the receiver=None, this means it must be sent to all agents. This function will process
         the receiver=None to a seperate message directed at every agent.

        Parameters
        ----------
        tick : int
            Current tick of the gridworld
        messages : dict
            All messages sent from the agent brains in the gridworld, and received via the api
        all_agent_ids : list
            IDs of all the agents
        teams : list
            ...

        -------
        """
        self.teams = teams

        # create private chats for any new agents
        if self.agents != all_agent_ids or not self.initialized_chatrooms:
            self.initialized_chatrooms = True
            # create private chats
            self._create_chatrooms(all_agent_ids)

        self.agents = all_agent_ids

        # set the agent IDs of the global chat to be all agent IDs
        self.chatrooms[0].agent_IDs = self.agents

        # init a list for the messages this tick
        if tick not in self.preprocessed_messages and len(messages) != 0:
            self.preprocessed_messages[tick] = []

        # process every message
        for mssg in messages:

            # check the message for validity
            MessageManager.__check_message(mssg, mssg.from_id)

            # decode the receiver_string into agent / team / global messages, save seperatly, and split into individual
            # messages understandable by the GridWorld
            self._decode_message_receiver(mssg, all_agent_ids, teams, tick)


    def _decode_message_receiver(self, mssg, all_agent_ids, teams, tick):
        """ Processes messages directed at other agents / teams / everyone.

        Messages are saved in chatroom objects, which have a name and ID.
        All messages are processed into their individual messages as well and
        saved in a seperate list (`self.preprocess_messages`) with all
        preprocessed messages suitable for sending by the GridWorld.

        Possible formats for mssg.to_id
        "agent1"                  = private message to agent1 + team "agent1" if it exists
        ["agent1", "agent2"]      = 2 private messages + team messages if likewise named teams exist
        "team2"                   = team message sent to everyone in that team
        '["agent3", "team4"]'     = team + agent message. Provided as a string via the api
        None                      = global message send to everyone

        Parameters
        ----------
        mssg
            The original mssg object sent by the agent, or received via the api
        all_agent_ids
            List with IDs of all agents
        teams
            Dict with all team names (keys), and a list with all agent IDs in that team (value)
        tick
            Current tick of the gridworld
        """
        all_ids_except_me = [agent_id for agent_id in all_agent_ids if agent_id != mssg.from_id]

        # Make sure that the message has a unique ID, and keep its custom class / properties
        new_mssg = copy.copy(mssg)
        new_mssg.regen_id()
        new_mssg.tick = tick

        # if the receiver is None, it is a global message which has to be sent to everyone
        if mssg.to_id is None:
            # save a copy in global
            global_message = self.copy_message(mssg=mssg, from_id=mssg.from_id, to_id="global")
            self.chatrooms[0].add_message(global_message)

            # split in sub mssgs
            for to_id in all_ids_except_me.copy():
                # create message
                new_message = self.copy_message(mssg=mssg, from_id=mssg.from_id, to_id=to_id)

                # save in preprocessed, which is all individual messages combined
                self.preprocessed_messages[tick].append(new_message)

        # if it is a list, decode every receiver_id in that list again
        elif isinstance(mssg.to_id, list):
            for receiver_id in mssg.to_id:
                # create message
                new_message = self.copy_message(mssg=mssg, from_id=mssg.from_id, to_id=receiver_id)
                # decode as individual messages
                self._decode_message_receiver(new_message, all_agent_ids, teams, tick)

        # a string might be: a list encoded as a string, a team, or an agent_id.
        elif isinstance(mssg.to_id, str):
            is_team_message = False

            try:
                # check if it is a list encoded as a string (sent via api)
                to_ids = eval(mssg.to_id)

                # create a new message addressed to this list of IDs, and reprocess
                new_message = self.copy_message(mssg=mssg, from_id=mssg.from_id, to_id=to_ids)
                self._decode_message_receiver(new_message, all_agent_ids, teams, tick)
            except:
                pass


            # Check if mssg_to is a team name. Note: an agent can only send a message to a team if they are in it.
            if mssg.to_id in teams.keys() and mssg.from_id in teams[mssg.to_id]:
                is_team_message = True

                # get the ID of the chatroom if already exists
                chatroom_ID = self.fetch_chatroom_ID(chatroom_type="team", team_name=mssg.to_id)

                # create the chatroom if it doesn't exist yet
                if chatroom_ID is False:
                    chatroom_ID = len(self.chatrooms)
                    chatroom = Chatroom(ID=chatroom_ID, name=mssg.to_id,
                                    type="team", agent_IDs=teams[mssg.to_id])
                    self.chatrooms.append(chatroom)

                # register what the index of this message is in the chatroom
                mssg.chat_mssg_count = len(self.chatrooms[chatroom_ID].messages)

                # save the mssg to the chatroom
                self.chatrooms[chatroom_ID].add_message(mssg)

                # split in sub mssgs for every agent in the team
                for to_id in teams[mssg.to_id]:
                    # create a message
                    new_message = self.copy_message(mssg=mssg, from_id=mssg.from_id, to_id=to_id)
                    # save in prepr
                    self.preprocessed_messages[tick].append(new_message)

            # check if it is an agent ID (as well)
            # If no team is set by the user, the agent is added to a new team with the same name as the agent's ID.
            # As such, a message can be targeted at a team and individual agent at the same time.
            if mssg.to_id in all_agent_ids:

                # get the ID of the chatroom if already exists
                chatroom_ID = self.fetch_chatroom_ID(chatroom_type="private", agent_IDs=[mssg.to_id, mssg.from_id])

                # create the chatroom if it doesn't exist yet
                if chatroom_ID is False:
                    # The name of a private chat are the IDs of both agents
                    #  alphabetically concatenated and split with a underscore
                    ids_sorted = [mssg.to_id, mssg.from_id]
                    ids_sorted.sort()
                    private_chatroom_name = ids_sorted[0] + "__" + ids_sorted[1]

                    # add the chatroom
                    chatroom_ID = len(self.chatrooms)
                    chatroom = Chatroom(ID=chatroom_ID, name=private_chatroom_name,
                            type="private", agent_IDs=[mssg.to_id, mssg.from_id])
                    self.chatrooms.append(chatroom)

                # register what the index of this message is in this private chatroom
                mssg.chat_mssg_count = len(self.chatrooms[chatroom_ID].messages)

                # save the mssg to the chatroom
                self.chatrooms[chatroom_ID].add_message(mssg)

                # if the message was not already saved in the preprocessed list, save it there as well
                if not is_team_message:
                    new_message = self.copy_message(mssg=mssg, from_id=mssg.from_id, to_id=mssg.to_id)
                    self.preprocessed_messages[tick].append(new_message)



    def fetch_chatroom_ID(self, chatroom_type, agent_IDs=[], team_name=False):
        """ Fetch the ID of a chatroom using various bits of info

        Parameters
        ----------
        chatroom_type : str
            Either "private" for private charooms send between 2 agents, or
            "team" for messages between teams.
        agent_IDs : list (optional)
            List of the agent IDs part of that chatroom
        team_name : str (optional)
            The name of the team, which is used as chatroom name
        """

        if chatroom_type == "private":
            # The name of a private chat is the two agent IDs concatenated
            # alphabetically with an underscore
            ids_sorted = list(agent_IDs)
            ids_sorted.sort()
            private_chat_name = ids_sorted[0] + "__" + ids_sorted[1]

            # return the chatroom ID of the chatroom with that name
            for chatroom in self.chatrooms:
                if chatroom.name == private_chat_name:
                    return chatroom.ID

        elif chatroom_type == "team":
            for chatroom in self.chatrooms:

                # fetch the ID of a team chat by name
                if chatroom.type == chatroom_type and chatroom.name == team_name:
                    return chatroom.ID

        return False


    def _create_chatrooms(self, all_agent_ids):
        """ Create any private chats not yet initialized for known agent pairs """
        # get all unique agent-agent combinations
        unique_agent_combinations = [comb for comb in combinations(all_agent_ids, 2)]

        # create a private chat for every agent-agent combination
        for unique_agent_combination in unique_agent_combinations:

            # get the ID of the chatroom if already exists
            chatroom_ID = self.fetch_chatroom_ID(chatroom_type="private", agent_IDs=unique_agent_combination)

            # create the chatroom if it doesn't exist yet
            if chatroom_ID is False:
                # The name of a private chat are the IDs of both agents
                #  alphabetically concatenated and split with a underscore
                ids_sorted = [unique_agent_combination[0], unique_agent_combination[1]]
                ids_sorted.sort()
                private_chatroom_name = ids_sorted[0] + "__" + ids_sorted[1]

                chatroom_ID = len(self.chatrooms)
                chatroom = Chatroom(ID=chatroom_ID, name=private_chatroom_name,
                        type="private", agent_IDs=[ids_sorted[0], ids_sorted[1]])
                self.chatrooms.append(chatroom)


        # create the team chatrooms
        for team_name, team_members in self.teams.items():
            # get the ID of the chatroom if already exists
            chatroom_ID = self.fetch_chatroom_ID(chatroom_type="team", team_name=team_name)

            # create the chatroom if it doesn't exist yet
            if chatroom_ID is False:
                chatroom_ID = len(self.chatrooms)
                chatroom = Chatroom(ID=chatroom_ID, name=team_name,
                                    type="team", agent_IDs=team_members)
                self.chatrooms.append(chatroom)
        return


    @staticmethod
    def __check_message(mssg, this_agent_id):
        if not isinstance(mssg, Message):
            raise Exception(f"A message to {this_agent_id} is not, nor inherits from, the class {Message.__name__}."
                            f" This is required for agents to be able to send and receive them.")


    def fetch_chatrooms(self, agent_id=None):
        """ Fetch all the chatrooms, or only those of which a specific agent is part.

        Parameters
        ----------
        agent_id : str (optional, default, None)
            ID of the agent for which to fetch all accessible chatrooms. if None, all chatrooms are returned.

        Returns
        -------
        chatrooms : dict
            A dictionary containing a list with all "private" chatrooms, all "teams" chatrooms, and a "global" key,
            accessible via likewise named keys.
        """

        chatrooms = {}

        # create a dict with chatroom IDs and chatroom names for all relevant
        # chatrooms
        for chatroom in self.chatrooms:
            chatroom_ID = chatroom.ID
            # add the chatroom if not agent_id was passed, or
            # the agent is present in the chat
            if agent_id is None or agent_id in chatroom.agent_IDs or agent_id == "god":
                chatrooms[chatroom_ID] = {"name": chatroom.name, "type": chatroom.type}

        return chatrooms



    def fetch_messages(self, agent_id=None, chatroom_mssg_offsets=None):
        """ Fetch messages, optionally filtered by start tick and/or agent id.

        Parameters
        ----------
        agent_id : string (optional, default=None)
            Only messages received by or sent by this agent will be collected. If none, all messages
            will be returned.

        chatroom_mssg_offsets: dict (optional, default=None)
            A dict of chat IDs, with for each ID from which message onward to send new messages.


        Returns
        -------
        Chatrooms : dict
            Dictionary with as key the chatroom IDs, followed by the chatroom objects containing
            among others the chatroom messages.

        """
        chatrooms = {}

        if chatroom_mssg_offsets is None:
            chatroom_mssg_offsets = {}

        # fetch the relevant chatrooms for this agent (or all)
        chatroom_IDs = self.fetch_chatrooms(agent_id=agent_id).keys()

        for chatroom_ID in chatroom_IDs:

            # data is sent as JSON to the API, which makes the keys of objects/dicts strings by
            # default, so convert the chatroom ID temporarily to str to find a match
            str_chatroom_ID = str(chatroom_ID)

            # send only the messages in this chatroom from the offset onwards
            if str_chatroom_ID in chatroom_mssg_offsets.keys():
                offset = chatroom_mssg_offsets[str_chatroom_ID]
                # start with the first message if it is none
                if offset is None:
                    offset = -1

                # if the offset is X, we want messages with index > X (if they exist)
                if offset + 1 < len(self.chatrooms[chatroom_ID].messages):
                    chatrooms[chatroom_ID] = self.chatrooms[chatroom_ID].messages[offset + 1:]
                else:
                    chatrooms[chatroom_ID] = []

            # otherwise just send all messages for this chatroom
            else:
                chatrooms[chatroom_ID] = self.chatrooms[chatroom_ID].messages

            # convert each message to json
            chatrooms[chatroom_ID] = [mssg.to_json() for mssg in chatrooms[chatroom_ID]]

        return chatrooms


    def copy_message(self, mssg, from_id, to_id):
        """ Copy a message while keeping the potentially custom message type and custom message properties.
        Global and team messages have to be subdivided into individual messages for each receiving agent.
        This function copies a message while paying attention to any custom message classes used and their custom
        properties, in addition to making sure the message has a unique message ID.

        Parameters
        ----------
        mssg : (Custom)Message
            original message instance. Can be the default Message() class, or a class that inherits from it.
        from_id : str
            the new sender ID.
        to_id : str
             the new receiver ID.

        Returns
        new_mssg : (Custom)Message
            the new message instance with the same class and custom properties as mssg, with the provided from_id
            and to_id.
        -------
        """
        # copy the original message so we are sure we have the correct message class
        new_mssg = copy.copy(mssg)#

        # make sure the new message has a unique ID
        new_mssg.regen_id()

        # set the new from and to ID
        new_mssg.from_id = from_id
        new_mssg.to_id = to_id

        return new_mssg


class Chatroom:
    """ A chatroom object, containing the messages from various agents from that chatroom. """

    def __init__(self, ID, name, type="private", agent_IDs = []):
        """ Add a message to the chatroom

        Parameters
        ----------
        mssg : Message
            The message to be added
        """
        self.ID = ID
        self.messages = []
        self.name = name
        self.type = type
        self.agent_IDs = agent_IDs

    def add_message(self, mssg):
        """ Add a message to the chatroom

        Parameters
        ----------
        mssg : Message
            The message to be added
        """
        # register what the index of this message is in the chatroom
        mssg.chat_mssg_count = len(self.messages)

        # add the message
        self.messages.append(mssg)
