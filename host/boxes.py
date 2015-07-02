from pycboard import Pycboard 
from config import *

class Boxes():
    '''Provides functionallity for doing operations on a group of Pycboards.'''

    def __init__(self, box_numbers, hardware): 
        self.hw = hardware
        self.boxes = {}
        for box_n in box_numbers:
            self.boxes[box_n] = Pycboard(box_serials[box_n])

    def setup_state_machine(self, sm_name, sm_dir = None):
        for box in self.boxes.values():
            box.setup_state_machine(sm_name, self.hw, sm_dir)

    def start_framework(self, dur = None, verbose = False, data_output = True):
        for box in self.boxes.values():
            box.start_framework(dur, verbose, data_output)        

    def load_framework(self):
        for box in self.boxes.values():
            box.load_framework()

    def process_data(self):
        for box in self.boxes.values():
            box.process_data()

    def stop_framework(self):
        for box in self.boxes.values():
            box.stop_framework()

    def print_IDs(self):
        for box in self.boxes.values():
            box.print_IDs()

    def set_variables(self):
        pass

    def open_data_file(self, file_names, sub_dir = None):
        for box_n in self.boxes.keys():
            self.boxes[box_n].open_data_file(file_names[box_n], sub_dir)

    def close_data_file(self):
        for box in self.boxes.values():
            box.close_data_file()

    def close(self):
        for box in self.boxes.values():
            box.close()









