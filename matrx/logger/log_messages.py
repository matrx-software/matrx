from matrx.logger.logger import GridWorldLogger, GridWorldLoggerV2
import copy
import json


class MessageLogger(GridWorldLogger):
    """ Logs messages send and received by (all) agents """

    def __init__(self, save_path="", file_name_prefix="", file_extension=".csv", delimeter=";"):
        super().__init__(save_path=save_path, file_name=file_name_prefix, file_extension=file_extension,
                         delimiter=delimeter, log_strategy=1)
        # IDs of the agents we want to log messages of
        self.agent_ids = []
        self.agent_ids_initialized = False
        self.log_statement_template = {'correct_tick': 0}

    def log(self, grid_world, agent_data):

        # find the IDs of the agents we need to log and create a template log statement
        if not self.agent_ids_initialized:
            for agent_id in grid_world.registered_agents.keys():
                self.agent_ids.append(agent_id)

                # create a field for messages sent and messages received
                self.log_statement_template[agent_id + "_sent"] = None
                self.log_statement_template[agent_id + "_received"] = None
                # field specific for logging the entire message as json
                self.log_statement_template[agent_id + "_mssg_json"] = None

            self.agent_ids_initialized = True

        # create a copy of the log template for the messages of the tick we are now processing
        log_statement = copy.copy(self.log_statement_template)

        # we check the messages of the previous tick, as the messages of this tick haven't been processed yet
        tick_to_check = grid_world.current_nr_ticks-1
        log_statement['correct_tick'] = tick_to_check

        if tick_to_check in grid_world.message_manager.preprocessed_messages.keys():
            # loop through all messages of this tick
            for message in grid_world.message_manager.preprocessed_messages[tick_to_check]:

                # optional: filter only specific types of messages or specific agents here

                # Log the message content for the sender and receiver
                log_statement[message.from_id + "_sent"] = message.content
                log_statement[message.to_id + "_received"] = message.content

                # log the entire message to json as a dict
                log_statement[message.from_id + "_mssg_json"] = json.dumps(message.__dict__)

        return log_statement


class MessageLoggerV2(GridWorldLoggerV2):
    """ Logs messages send and received by (all) agents """

    def __init__(self, save_path="", file_name_prefix="", file_extension=".csv", delimeter=";"):
        super().__init__(save_path=save_path, file_name=file_name_prefix, file_extension=file_extension,
                         delimiter=delimeter, log_strategy=1)
        # IDs of the agents we want to log messages of
        self.agent_ids = []
        self.agent_ids_initialized = False
        self.log_statement_template = {'correct_tick': 0}

    def log(self, world_state, agent_data, grid_world):
        # find the IDs of the agents we need to log and create a template log statement
        if not self.agent_ids_initialized:
            for agent_id in grid_world.registered_agents.keys():
                self.agent_ids.append(agent_id)

                # create a field for messages sent and messages received
                self.log_statement_template[agent_id + "_sent"] = None
                self.log_statement_template[agent_id + "_received"] = None
                # field specific for logging the entire message as json
                self.log_statement_template[agent_id + "_mssg_json"] = None

            self.agent_ids_initialized = True

        # create a copy of the log template for the messages of the tick we are now processing
        log_statement = copy.copy(self.log_statement_template)

        # we check the messages of the previous tick, as the messages of this tick haven't been processed yet
        tick_to_check = grid_world.current_nr_ticks-1
        log_statement['correct_tick'] = tick_to_check

        if tick_to_check in grid_world.message_manager.preprocessed_messages.keys():
            # loop through all messages of this tick
            for message in grid_world.message_manager.preprocessed_messages[tick_to_check]:

                # optional: filter only specific types of messages or specific agents here

                # Log the message content for the sender and receiver
                log_statement[message.from_id + "_sent"] = message.content
                log_statement[message.to_id + "_received"] = message.content

                # log the entire message to json as a dict
                log_statement[message.from_id + "_mssg_json"] = json.dumps(message.__dict__)

        return log_statement
