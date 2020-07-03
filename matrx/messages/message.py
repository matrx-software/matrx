import json
import random


class Message:
    """
    A simple object representing a communication message. An agent can create such a Message object by stating the
    content, its own id as the sender and (optional) a receiver. If a receiver is not given it is a message to all
    agents, including the sender.
    NOTE: this Message class is also used by the MATRX api

    Possible formats for mssg.to_id
    "agent1"                  = individual message to agent1 + message to team "agent1" if it exists
    ["agent1", "agent2"]      = 2 individual messages + 2 team messages if likewise named teams exist
    "team2"                   = team message. A team message is sent to everyone in that team
    '["agent3", "team4"]'     = team + agent message. Provided as a string via the api
    None                      = global message. This message is send to everyone
    """

    def __init__(self, content, from_id, to_id=None):
        """ Creates a message

        Parameters
        ----------
        content : anything
           Denotes the content of the message, can be anything: a string, dict, custom object, etc. As long
           as it is JSON serializable.
        from_id : str
           The ID who sent this message.
        to_id : str or list (optional, default, None)
           The ID to who to sent this message. If None, the message will be sent to all agents excluding the sender.
        """
        self.content = content  # content can be anything; a string, a dictionary, or even a custom object
        self.from_id = from_id  # the agent id who creates this message
        self.to_id = to_id  # the agent id who is the sender, when None it means all agents, including the sender
        self.message_id = self.__gen_random_string()  # randomly generated ID of the message

    def to_json(self):
        """ Make this class JSON serializable, such that it can be sent as JSON via the api """
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def regen_id(self):
        """ Regenerates the message ID.
        When someone copies this message, by default the message_id is not changed. To avoid duplicate mssg IDs, this
        message can be called to change the regen the ID of a message.

        Examples
        ---------
        >>> print(mssg.message_id) # output: 242523098cb176b4
        >>> mssg.regen_id()
        >>> print(mssg.message_id) # output: 484de0a68fed7579
        """
        self.message_id = self.__gen_random_string()

    @staticmethod
    def __gen_random_string(length=32):
        """ Generates a random hexidecimal string of length 'length'.

        Parameters
        ----------
        length
            Length of the hexidecimal string to return.

        Returns
        -------
            A random hexidecimal string of length 'length'.
        """
        return '%030x' % random.randrange(16**length)
