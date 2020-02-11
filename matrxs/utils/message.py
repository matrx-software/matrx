
from matrxs.utils.utils import gen_random_string

class Message:
    """
    A simple object representing a communication message. An agent can create such a Message object by stating the
    content, its own id as the sender and (optional) a receiver. If a receiver is not given it is a message to all
    agents, including the sender.
    NOTE: this Message class is also used by the MATRXS API

    Possible formats for mssg.to_id
    "agent1"                  = individual message to agent1 + message to team "agent1" if it exists
    ["agent1", "agent2"]      = 2 individual messages + 2 team messages if likewise named teams exist
    "team2"                   = team message. A team message is sent to everyone in that team
    '["agent3", "team4"]'     = team + agent message. Provided as a string via the API
    None                      = global message. This message is send to everyone
    """

    def __init__(self, content, from_id, to_id=None):
        self.content = content  # content can be anything; a string, a dictionary, or even a custom object
        self.from_id = from_id  # the agent id who creates this message
        self.to_id = to_id  # the agent id who is the sender, when None it means all agents, including the sender
        self.message_id = gen_random_string(30) # randomly generated ID of the message