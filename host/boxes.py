from pycboard import Pycboard 
from config import *

class Boxes():
    '''Provides functionallity for doing operations on a group of Pycboards.
    Most methods are a thin wrapper around the corresponding pycboard method.'''

    def __init__(self, box_numbers, hardware): 
        self.hw = hardware
        self.boxes = {}
        for box_ID in box_numbers:
            self.boxes[box_ID] = Pycboard(box_serials[box_ID])

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

    def set_variable(self, sm_name, v_name, v_value):
        '''Set specified variable on a all pyboards. If v_value is a
         dict whose keys match the box ID numbers, the variable on each
         box is set to the corresponding value from the dictionary.  Otherwise
         the variable on all boxes is set to v_value.
        '''
        if type(v_value) == dict and self.boxes.keys() == v_value.keys(): 
            for box_ID in self.boxes.keys():
                self.boxes[box_ID].set_variable(sm_name, v_name, v_value[box_ID])
        else:
            for box in self.boxes.values():
                box.set_variable(sm_name, v_name, v_value)

    def open_data_file(self, file_names, sub_dir = None):
        for box_ID in self.boxes.keys():
            self.boxes[box_ID].open_data_file(file_names[box_ID], sub_dir)

    def close_data_file(self):
        for box in self.boxes.values():
            box.close_data_file()

    def close(self):
        for box in self.boxes.values():
            box.close()









