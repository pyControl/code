import json
from collections import namedtuple
from source.communication.pycboard import MsgType


class Api:
    # ----------------------------------------------------------
    # Functions that the user can overwrite
    # ----------------------------------------------------------

    def __init__(self):
        """User Api class is initialised when the task is uploaded to the board"""
        pass

    def run_start(self):
        """Called once when the task is started"""
        pass

    def run_stop(self):
        """Called once when the task is stopped"""
        pass

    def process_data_user(self, data):
        """Called whenever there is a state transition, event
        or printed line. Gives the user access to data dictionary

        data : a dictionary with keys 'states', 'events' and 'prints', 'vars' and 'analog'
               and values a list of tuples in format
               (name of state or event / printed string, time)
        """
        pass

    def plot_update(self):
        """Called whenever the plots are updated
        The default plotting update interval is 10ms
        and can be adjusted in settings dialog
        """
        pass

    # ----------------------------------------------------------
    # User can call these functions
    # ----------------------------------------------------------

    def set_variable(self, v_name, v_value):
        """Call this function to change the value of a task variable.

        v_name : str
            name of variable to change
        v_value :
            value to change variable to
        """

        if v_name in self.board.sm_info.variables.keys():
            self.board.set_variable(v_name, v_value, source="a")
        else:
            self.print_to_log(
                f"Variable {v_name} not defined in task file {self.board.sm_info.name} so cannot be set by API"
            )

    def trigger_event(self, event):
        if event in self.board.sm_info.events.keys():
            self.board.trigger_event(event, "a")
        else:
            self.print_to_log(
                f"Event {event} not defined in task file {self.board.sm_info.name} so cannot be set by API"
            )

    def print_message(self, msg):
        self.board.data_logger.print_message(msg, "a")

    # Note:  get_variable functionality not implemented because board.get_variable method
    # does not return variable value when framework is running, just causes it to be output
    # by the board as soon as possible.

    # ----------------------------------------------------------
    # User should not overwrite or call these functions
    # ----------------------------------------------------------

    def interface(self, board, print_to_log):
        """Called once when task is uploaded and api is initialised.
        Gives api access to board object and print_to_log method
        """

        # Connect Api with pyboard and gui.
        self.board = board
        self.print_to_log = print_to_log
        self.ID2name = self.board.sm_info.ID2name
        self.ID2analog = {}  # Convert analog ID to name
        for ID, info in self.board.sm_info.analog_inputs.items():
            self.ID2analog[ID] = info["name"]

        # Declare the named tuples for the user friendly data
        # structure, so they are not newly declared with
        # each call to process_data
        self.event_tup = namedtuple("Event", "name time")
        self.state_tup = namedtuple("State", "name time")
        self.print_tup = namedtuple("Print", "data time")
        self.var_tup = namedtuple("Var", "name value time")
        self.analog_tup = namedtuple("Analog", "name data time")

    def process_data(self, new_data):
        """Called directly by the gui every time there is new data.
        receives new_data from the board and processes it to a user
        friendly data structure. Then passes new data structure to
        process_data_user.
        """

        data = {"states": [], "events": [], "prints": [], "vars": [], "analog": []}

        for nd in new_data:
            if nd.type == MsgType.PRINT:
                data["prints"].append(self.print_tup(nd.content, nd.time))
            elif nd.type == MsgType.VARBL:
                var_change_dict = json.loads(nd.content)
                name = list(var_change_dict.keys())[0]
                value = list(var_change_dict.values())[0]
                data["vars"].append(self.var_tup(name, value, nd.time))
            elif nd.type == MsgType.STATE:
                name = self.ID2name[nd.content]
                data["states"].append(self.state_tup(name, nd.time))
            elif nd.type == MsgType.EVENT:
                name = self.ID2name[nd.content]
                data["events"].append(self.event_tup(name, nd.time))
            elif nd.type == MsgType.ANLOG:
                data["analog"].append(self.analog_tup(self.ID2analog[nd.content[0]], nd.content[1], nd.time))

        self.process_data_user(data)
