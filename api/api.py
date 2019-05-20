class Api():
    '''list of the function availble to api classes'''
    def __init__(self):
        pass

    def interface(self, board, print_to_log):
        # Connect Api with pyboard and gui.
        self.board = board
        self.print_to_log = print_to_log
        self.ID2name = self.board.sm_info['ID2name']

    def set_state_machine(self,sm_info):
        pass

    def run_start(self, recording):
        pass

    def run_stop(self):
        pass

    def update(self):
        pass

    def process_data(self, new_data):
        pass

    def set_variable(self, v_name, v_value):
        self.board.set_variable(v_name, v_value)

    # Note:  get_variable functionality not implemented because board.get_variable method 
    # does not return variable value when framework is running, just causes it to be output
    # by the board as soon as possible.