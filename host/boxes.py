from pycboard import Pycboard 
from pprint import pformat
import os
import config.config as config

class Boxes():
    '''Provides functionallity for doing operations on a group of Pycboards.
    Most methods are a thin wrapper around the corresponding pycboard method.'''

    def __init__(self, box_numbers, hardware = None): 
        self.hw = hardware
        self.boxes = {}
        for box_ID in box_numbers:
            print('Opening connection to box {}'.format(box_ID))
            self.boxes[box_ID] = Pycboard(config.box_serials[box_ID], box_ID)
        self.unique_IDs = {box_ID: self.boxes[box_ID].unique_ID
                                   for box_ID in self.boxes}

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
            n_boxes_running = 0
            if box.framework_running:
                box.process_data()
                n_boxes_running += 1
        return n_boxes_running > 0

    def stop_framework(self):
        for box in self.boxes.values():
            box.stop_framework()

    def print_IDs(self):
        for box in self.boxes.values():
            box.print_IDs()

    def set_variable(self, sm_name, v_name, v_value):
        '''Set specified variable on a all pycboards. If v_value is a
         dict whose keys include all the box ID numbers, the variable on each
         box is set to the corresponding value from the dictionary.  Otherwise
         the variable on all boxes is set to v_value.
        '''
        if type(v_value) == dict and set(self.boxes.keys()) <= set(v_value.keys()): 
            for box_ID in self.boxes.keys():
                self.boxes[box_ID].set_variable(sm_name, v_name, v_value[box_ID])
        else:
            for box in self.boxes.values():
                box.set_variable(sm_name, v_name, v_value)

    def get_variable(self, sm_name, v_name):
        '''Get value of specified variable from all boxes and return as dict with 
        box numbers as keys.'''
        v_values = {}
        for box_ID in self.boxes.keys():
            v_values[box_ID] = self.boxes[box_ID].get_variable(sm_name, v_name)
        return v_values

    def open_data_file(self, file_names, sub_dir = None):
        for box_ID in self.boxes.keys():
            self.boxes[box_ID].open_data_file(file_names[box_ID], sub_dir)

    def close_data_file(self, copy_to_transfer = False):
        for box in self.boxes.values():
            box.close_data_file(copy_to_transfer)

    def close(self):
        for box in self.boxes.values():
            box.close()

    def write_to_file(self, write_string):
        for box in self.boxes.values():
            box.data_file.write(write_string)

    def save_unique_IDs(self):
        print('Saving hardware unique IDs.')
        with open(os.path.join('config', 'hardware_unique_IDs.txt'), 'w') as id_file:        
                id_file.write(pformat(self.unique_IDs))

    def check_unique_IDs(self):
        '''Check whether hardware unique IDs of pyboards match those saved in 
        config.hardware_unique_IDs, if file not available no checking is performed.'''
        try:
            with open(os.path.join('config', 'hardware_unique_IDs.txt'), 'r') as id_file:        
                unique_IDs = eval(id_file.read())
        except FileNotFoundError:
            print('\nNo hardware IDs saved, skipping hardware ID check.')
            return True          
        print('\nChecking hardware IDs...  ', end = '')
        IDs_OK = True
        for box_ID in self.boxes.keys():
            if unique_IDs[box_ID] != self.unique_IDs[box_ID]:
                print('\nBox number {} does not match saved unique ID.'.format(box_ID))
                IDs_OK = False
        if IDs_OK: print('IDs OK.')
        return IDs_OK




