import os
from time import sleep
from pprint import pformat

from .pycboard import Pycboard 
from .pyboard import PyboardError

import config.config as config
from config.paths import tasks_dir, config_dir

class Pycboards():
    'Perform operations on a group of Pycboards.'

    def __init__(self, board_numbers): 
        self.boards = {}
        self.board_numbers = sorted(board_numbers)
        for board_n in board_numbers:
            print('Opening connection to board {}'.format(board_n))
            self.boards[board_n] = Pycboard(config.board_serials[board_n], raise_exception=True)
        self.unique_IDs = {board_n: self.boards[board_n].unique_ID for board_n in self.boards}

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
        for board_n in self.board_numbers:
            self.boards[board_n].start_framework(dur, data_output)
            if ISI:
                sleep(ISI)  # Stagger start times by ISI seconds.       
                self.boards[board_n].process_data()

    def load_framework(self):
        for board in self.boards.values():
            board.load_framework()

    def load_hardware_definition(self):
        for board in self.boards.values():
            board.load_hardware_definition()            

    def process_data(self):
        boards_running = False
        for board in self.boards.values():
            if board.framework_running:
                boards_running = True
            try:
                board.process_data(raise_exception=True)
            except PyboardError:
                self.board_errors.append(board.number)
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
            for board_n in self.board_numbers:
                self.boards[board_n].set_variable(v_name, v_value[board_n])
        else:
            for board in self.boards.values():
                board.set_variable(v_name, v_value)

    def get_variable(self, v_name):
        '''Get value of specified variable from all boards and return as dict with 
        board numbers as keys.'''
        v_values = {}
        for board_n in self.board_numbers:
            v_values[board_n] = self.boards[board_n].get_variable(v_name)
        return v_values

    def open_data_file(self, file_paths):
        for board_n in self.board_numbers:
            self.boards[board_n].open_data_file(file_paths[board_n])

    def close_data_file(self):
        for board in self.boards.values():
            board.close_data_file()

    def close(self):
        for board in self.boards.values():
            board.close()

    def write_to_file(self, write_string, end='\n'):
        '''Write write_string to each boards data file.  If write_string is a dict
        whose keys include all the board ID numbers, the corresponding values are
        written to each board.'''
        if type(write_string) == dict and set(self.boards.keys()) == set(write_string.keys()): 
            for board_n in self.board_numbers:
                self.boards[board_n].write_to_file(write_string[board_n],end)
        else:
            for board in self.boards.values():
                board.write_to_file(write_string,end)

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
        for board_n in self.board_numbers:
            if unique_IDs[board_n] != self.unique_IDs[board_n]:
                print('\nBox number {} does not match saved unique ID.'.format(board_n))
                IDs_OK = False
        if IDs_OK: print('IDs OK.')
        return IDs_OK