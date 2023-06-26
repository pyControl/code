from collections import namedtuple


class Api:
    # ----------------------------------------------------------
    # Functions that the user can overwrite
    # ----------------------------------------------------------

    def __init__(self):
        """User Api class is initialised when the task is uploaded to the board """
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

        data : a dictionary with keys 'states', 'events' and 'prints'
               and values a list of tuples in format
               (name of state or event / printed string, time)
        """
        pass

    def update(self):
        """Called several times / second regardless of whether
        there is a state transition or event.

        The user should be cautious when overwriting this function
        as code that does not execute in sub-millisecond time will
        impact the performance of pyControl
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

        if v_name in self.board.sm_info["variables"].keys():
            self.board.set_variable(v_name, v_value)
        else:
            self.print_to_log(
                f"Variable {v_name} not defined in task file {self.board.sm_info['name']} so cannot be set by API"
            )

    def generate_event(self, event):
        if event in self.board.sm_info["events"].keys():
            self.board.generate_event(event)
        else:
            self.print_to_log(
                f"Variable {event} not defined in task file {self.board.sm_info['name']} so cannot be set by API"
            )

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
        self.ID2name = self.board.sm_info["ID2name"]
        self.ID2analog = {}  # Convert analog ID to name
        for name, info in self.board.sm_info["analog_inputs"].items():
            self.ID2analog[info["ID"]] = name

        # Declare the named tuples for the user friendly data
        # structure, so they are not newly declared with
        # each call to process_data
        self.event_tup = namedtuple("Event", "name time")
        self.state_tup = namedtuple("State", "name time")
        self.print_tup = namedtuple("Print", "name time")
        self.var_tup = namedtuple("Var", "name time")
        self.analog_tup = namedtuple("Analog", "name time data")

    def process_data(self, new_data):
        """Called directly by the gui every time there is new data.
        receives new_data from the board and processes it to a user
        friendly data structure. Then passes new data structure to
        process_data_user.
        """

        data = {"states": [], "events": [], "prints": [], "vars": [], "analog": []}

        for nd in new_data:
            if nd[0] == "P":
                data["prints"].append(self.print_tup(nd[2], nd[1]))
            elif nd[0] == "V":
                data["vars"].append(self.var_tup(nd[2], nd[1]))
            elif nd[0] == "D":
                name = self.ID2name[nd[2]]
                if name in self.board.sm_info["states"]:
                    data["states"].append(self.state_tup(name, nd[1]))
                else:
                    data["events"].append(self.event_tup(name, nd[1]))
            elif nd[0] == "A":
                data["analog"].append(self.analog_tup(self.ID2analog[nd[1]], nd[3], nd[4]))

        self.process_data_user(data)