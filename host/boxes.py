from pycboard import Pycboard 
from pprint import pformat
import os
import config.config as cf
from time import sleep

class Boxes():
    'Provides functionallity for doing operations on a group of Pycboards.'

    def __init__(self, box_numbers): 
        self.boxes = {}
        self.box_numbers = sorted(box_numbers)
        for box_n in box_numbers:
            print('Opening connection to box {}'.format(box_n))
            self.boxes[box_n] = Pycboard(cf.box_serials[box_n], box_n)
        self.unique_IDs = {box_n: self.boxes[box_n].unique_ID
                                   for box_n in self.boxes}

    def reset(self):
        for box in self.boxes.values():
            box.reset()        

    def setup_state_machine(self, sm_name, sm_dir = None):
        for box in self.boxes.values():
            box.setup_state_machine(sm_name, sm_dir)

    def start_framework(self, dur = None, verbose = False, data_output = True, ISI = 0.1):
        for box_n in self.box_numbers:
            self.boxes[box_n].start_framework(dur, verbose, data_output)
            if ISI:sleep(ISI)  # Stagger start times by ISI seconds.       

    def load_framework(self):
        for box in self.boxes.values():
            box.load_framework()

    def load_hardware_definition(self):
        for box in self.boxes.values():
            box.load_hardware_definition()            

    def process_data(self):
        for box in self.boxes.values():
            n_boxes_running = 0
            if box.framework_running:
                box.process_data()
                n_boxes_running += 1
        return n_boxes_running > 0

    def run_framework(self, dur = None, verbose = False):
        self.start_framework(dur, verbose)
        try:
            while self.process_data():
                pass
        except KeyboardInterrupt:
            self.stop_framework()

    def stop_framework(self):
        for box in self.boxes.values():
            box.stop_framework()

    def print_IDs(self):
        for box in self.boxes.values():
            box.print_IDs()

    def set_variable(self, v_name, v_value, sm_name = None):
        '''Set specified variable on a all pycboards. If v_value is a
         dict whose keys include all the box ID numbers, the variable on each
         box is set to the corresponding value from the dictionary.  Otherwise
         the variable on all boxes is set to v_value.
        '''
        if type(v_value) == dict and set(self.boxes.keys()) <= set(v_value.keys()): 
            for box_n in self.box_numbers:
                self.boxes[box_n].set_variable(v_name, v_value[box_n], sm_name)
        else:
            for box in self.boxes.values():
                box.set_variable(v_name, v_value, sm_name)

    def get_variable(self, v_name, sm_name = None):
        '''Get value of specified variable from all boxes and return as dict with 
        box numbers as keys.'''
        v_values = {}
        for box_n in self.box_numbers:
            v_values[box_n] = self.boxes[box_n].get_variable(v_name, sm_name)
        return v_values

    def open_data_file(self, file_paths):
        for box_n in self.box_numbers:
            self.boxes[box_n].open_data_file(file_paths[box_n])

    def close_data_file(self):
        for box in self.boxes.values():
            box.close_data_file()

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
        config/hardware_unique_IDs.txt, if file not available no checking is performed.'''
        try:
            with open(os.path.join('config', 'hardware_unique_IDs.txt'), 'r') as id_file:        
                unique_IDs = eval(id_file.read())
        except FileNotFoundError:
            print('\nNo hardware IDs saved, skipping hardware ID check.')
            return True          
        print('\nChecking hardware IDs...  ', end = '')
        IDs_OK = True
        for box_n in self.box_numbers:
            if unique_IDs[box_n] != self.unique_IDs[box_n]:
                print('\nBox number {} does not match saved unique ID.'.format(box_n))
                IDs_OK = False
        if IDs_OK: print('IDs OK.')
        return IDs_OK




