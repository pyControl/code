import os
from time import sleep
from pprint import pformat
from .pycboard import Pycboard 
from .pyboard import PyboardError
from com.data_logger import Data_logger
import config.config as config
from config.paths import tasks_dir, config_dir

def print_func_factory(n):
    # Returns function which prepend each line of print string with box number n.
    def print_func(s, end='\n'):
        s = 'Box {}: '.format(n) + s[:-1].replace('\n', '\nBox {}: '.format(n)) + '\n'
        print(s, end=end)
    return print_func

# Pycboards --------------------------------------------------------------------------

class Pycboards():
    'Perform operations on a group of Pycboards.'

    def __init__(self, numbers): 
        self.boards = {}
        self.numbers = sorted(numbers)
        for n in numbers:
            print('\nOpening connection to board {}'.format(n))
            self.boards[n] = Pycboard(config.board_serials[n], 
                data_logger=Data_logger(print_func=print_func_factory(n)))
        self.unique_IDs = {n: self.boards[n].unique_ID for n in self.boards}

    def reset(self):
        for board in self.boards.values():
            board.reset()       

    def hard_reset(self):
        for board in self.boards.values():
            board.hard_reset()   

    def reset_filesystem(self):
        for board in self.boards.values():
            board.reset_filesystem()

    def setup_state_machine(self, sm_name, sm_dir=tasks_dir):
        for board in self.boards.values():
            board.setup_state_machine(sm_name, sm_dir)

    def start_framework(self, dur=None, data_output=True, ISI=False):
        for n in self.numbers:
            self.boards[n].start_framework(dur, data_output)
            if ISI:
                sleep(ISI)  # Stagger start times by ISI seconds.       
                self.boards[n].process_data()

    def load_framework(self):
        for board in self.boards.values():
            board.load_framework()

    def load_hardware_definition(self):
        for board in self.boards.values():
            board.load_hardware_definition()            

    def process_data(self):
        boards_running = False
        for n, board in self.boards.items():
            if board.framework_running:
                boards_running = True
            try:
                board.process_data()
            except PyboardError:
                self.board_errors.append(n)
        return boards_running

    def run_framework(self, dur=None):
        self.board_errors = []
        self.start_framework(dur)
        try:
            while self.process_data():
                pass
        except KeyboardInterrupt:
            self.stop_framework()
        sleep(0.1)
        self.process_data()

    def stop_framework(self):
        for board in self.boards.values():
            board.stop_framework()

    def print_IDs(self):
        for board in self.boards.values():
            board.print_IDs()

    def set_variable(self, v_name, v_value):
        '''Set specified variable on a all pycboards. If v_value is a dict whose keys are
        the board ID numbers, the variable on each board is set to the corresponding value
        from the dictionary.  Otherwise the variable on all boards is set to v_value.'''
        if type(v_value) == dict and set(self.boards.keys()) == set(v_value.keys()): 
            for n in self.numbers:
                self.boards[n].set_variable(v_name, v_value[n])
        else:
            for board in self.boards.values():
                board.set_variable(v_name, v_value)

    def get_variable(self, v_name):
        '''Get value of specified variable from all boards and return as dict with 
        board numbers as keys.'''
        v_values = {}
        for n in self.numbers:
            v_values[n] = self.boards[n].get_variable(v_name)
        return v_values

    def open_data_file(self, data_dir, experiment_name, subject_IDs, datetime_now=None):
        for n, board in self.boards.items():
            board.data_logger.open_data_file(
                data_dir, experiment_name, subject_IDs[n], datetime_now)

    def get_file_paths(self):
        return {n:self.boards[n].data_logger.file_path for n in self.numbers}

    def close_data_file(self):
        for board in self.boards.values():
            board.data_logger.close_files()

    def close(self):
        for board in self.boards.values():
            board.close()

    def save_unique_IDs(self):
        print('Saving hardware unique IDs.')
        with open(os.path.join(config_dir, 'hardware_unique_IDs.txt'), 'w') as id_file:        
            id_file.write(pformat(self.unique_IDs))

    def check_unique_IDs(self):
        '''Check whether hardware unique IDs of pyboards match those saved in 
        config/hardware_unique_IDs.txt, if file not available no checking is performed.'''
        try:
            with open(os.path.join(config_dir, 'hardware_unique_IDs.txt'), 'r') as id_file:        
                unique_IDs = eval(id_file.read())
        except FileNotFoundError:
            print('\nNo hardware IDs saved, skipping hardware ID check.')
            return True          
        print('\nChecking hardware IDs...  ', end = '')
        IDs_OK = True
        for n in self.numbers:
            if unique_IDs[n] != self.unique_IDs[n]:
                print('\nBox number {} does not match saved unique ID.'.format(n))
                IDs_OK = False
        if IDs_OK: print('IDs OK.')
        return IDs_OK