from matrxs.agents.agent_brain import  Message

class MessageManager():
    """ A manager inside the GirdWorld that tracks the received and send messages between agents and their teams.

        This gives provides several advantages;
        - an easier connection between Core, API and Front-end for messages (e.g. to differentiate between messages send between agents and to teams in the Front-end through a simple API call: 'get_team_messages').
        - an easy way to log communication (as the messages are easily obtained from a GridWorld instance, through some methods).
    """

    def __init__(self):
        # the messages as specified in the agent / API
        self.messages_unprocessed = {} # all messages unprocessed

        # there are three types of messages
        self.global_messages = {} # messages send to everyone
        self.team_messages = {} # messages send to a team
        self.individual_messages = {} # messages send to individual agents

        self.preprocessed_messages = {} # all the types of messages above unpacked to the corresponding individual messages



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
        # safe the messages from this tick
        self.messages_unprocessed[tick] = messages

        # Messages can be sent from/to chats rooms: The global chat room (everyone), team rooms, or private chat rooms
        self.global_messages[tick] = []
        self.team_messages[tick] = {}
        for team in teams:
            self.team_messages[tick][team] = []
        self.individual_messages[tick] = []

        # the messages above all combined into one list
        self.preprocessed_messages[tick] = []

        # Possible input types:
        # "agent1"
        # ["agent1", "agent2"]
        # "team2"
        # '["agent3", "team4"]'
        # None

        # process every message
        for mssg in messages:
            sender_id = mssg.from_id
            all_ids_except_me = [agent_id for agent_id in all_agent_ids if agent_id != sender_id]

            # check the message for validity
            MessageManager.__check_message(mssg, sender_id)


    def _decode_message_receiver(self, mssg_to, all_agent_ids, all_ids_except_me, teams):
        """ Processes messages directed at other agents / teams / everyone

        Parameters
        ----------
        mssg_to
        all_agent_ids
        all_ids_except_me
        teams

        Returns
        -------

        """

        if mssg_to is None: # global message
            to_ids = all_ids_except_me.copy()
            message_type = "global"


            # todo: send messages
            # todo: save in global

        elif isinstance(mssg_to, list):
            for id in mssg_to:
                self._decode_message_receiver(mssg_to)

        elif isinstance(mssg_to, str):
            try:
                # check if it is a list encoded as a string (sent via API)
                ids = eval(mssg_to)
                self._decode_message_receiver(ids)
            except:
                pass

            # check if it is a team name
            if mssg_to in teams.keys():
                message_type = "team"


            # check if it is an agent ID (as well)
            if mssg_to in all_agent_ids:


            to_ids = [mssg.to_id]


        return to_ids

    def __process_message(self, agent_ids, message_type, tick, message_content):
        """ Create message objects in the correct chat rooms for a list of agent IDs.

        Parameters
        ----------
        ids
            List of agent IDs
        message_type
            Type of message: "global", "team" or "individual"
        """
        for agent_id in agent_ids:
            # Save the message to the correct message lists
            if message_type == "individual":  # messages from individual chat rooms
                self.individual_messages[tick].append(message_content)
            elif message_type == "team":  # messages within team chat rooms
                # the to_id is the team name
                self.team_messages[tick][agent_id].append(message_content)
            elif message_type == "global":  # messages in the global chatroom
                self.global_messages[tick].append(message_content)


        # todo: if sending to agent_id, make sure is not send to team instead by agent who is not in that team. Or is that allowable?

        # message_type = "individual"
        # # check the type of message
        # if mssg.to_id is None: # global message
        #     to_ids = all_ids_except_me.copy()
        #     message_type = "global"
        #
        # elif isinstance(mssg.to_id, list):
        #     for id in mssg.to_id:
        #
        # elif isinstance(mssg.to_id, str):
        #     try:
        #         ids = eval(ids)
        #     except:
        #         pass
        #
        #     # check if we have to send it to a team
        #     if mssg.to_id in teams.keys():
        #         message_type = "team"
        #
        #     to_ids = [mssg.to_id]
        #
        # elif isinstance(mssg.to_id, str)
        #
        # # otherwise its a list ?
        # else:
        #     print("mssg to id:", mssg.to_id, type(mssg.to_id))
        #     to_ids = mssg.to_id

    #     # Create a message object for each individual message
    #     for single_to_id in to_ids:
    #         new_message = Message(content=mssg.content, from_id=sender_id, to_id=single_to_id)
    #
    #         # Save the message to the correct message lists
    #         if message_type == "individual": # messages from individual chat rooms
    #             self.individual_messages[tick].append(new_message)
    #         elif message_type == "team": # messages within team chat rooms
    #             # the to_id is the team name
    #             self.team_messages[tick][mssg.to_id].append(new_message)
    #         elif message_type == "global": # messages in the global chatroom
    #             self.global_messages[tick].append(new_message)
    #
    #         self.preprocessed_messages[tick].append(new_message) # all messages above combined
    #
    # return self.preprocessed_messages

    @staticmethod
    def __check_message(mssg, this_agent_id):
        if not isinstance(mssg, Message):
            raise Exception(f"A message to {this_agent_id} is not, nor inherits from, the class {Message.__name__}."
                            f" This is required for agents to be able to send and receive them.")

    # @staticmethod
    # def preprocess_messages_old(this_agent_id, agent_ids, messages):
    #     """ Preprocess messages for sending, such that they can be understood by the GridWorld.
    #     For example: if the receiver=None, this means it must be sent to all agents. This function creates a message
    #     directed at every agent.
    #
    #     This is a static method such that it can also be accessed and used outside of this thread / the GridWorld loop.
    #     Such as by the API.
    #
    #     Note; This method should NOT be overridden!
    #
    #     Parameters
    #     ----------
    #     this_agent_id
    #         ID of the current agent, has to be sent as this is a static method
    #     agent_ids
    #         IDS of all agents known
    #     messages
    #         Messages which are to be processed
    #
    #     Returns
    #         Preprocessd messages ready for sending
    #     -------
    #     """
    #     # Filter out the agent itself from the agent id's
    #     agent_ids = [agent_id for agent_id in agent_ids if agent_id != this_agent_id]
    #
    #     # Loop through all Message objects and create a dict out of each and append them to a list
    #     preprocessed_messages = []
    #     for mssg in messages:
    #         # check message validity
    #         MessageManager.__check_message(mssg, this_agent_id)
    #
    #         # Check if the message is None (send to all agents) or single id; if so make a list out if
    #         if mssg.to_id is None:
    #             to_ids = agent_ids.copy()
    #         elif isinstance(mssg.to_id, str):
    #             to_ids = [mssg.to_id]
    #         else:
    #             to_ids = mssg.to_id
    #
    #         # For each receiver, create a Message object that wraps the actual object
    #         for single_to_id in to_ids:
    #             message = Message(content=mssg, from_id=this_agent_id, to_id=single_to_id)
    #
    #             # Add the message object to the messages
    #             preprocessed_messages.append(message)
    #
    #     return preprocessed_messages

