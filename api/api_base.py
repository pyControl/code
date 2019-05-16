import numpy as np
import sys
sys.path.append('..')
import api.user_classes

class Api_base():
    '''
    find the api class as defined in the task file, initialise it and
    provide interface between user class and basic Api class
    '''

    def __init__(self):
        self.api_used = False

    def set_state_machine(self, sm_info, print_func):
        '''
        find the api class defined in the task file, initialise it and
        set its state machine
       '''
        self.print_to_log = print_func
        if 'api_class' in sm_info['variables']:
            _user_class = sm_info['variables']['api_class']
            # using eval here to remove extra quote marks could maybe be an issue
            # if the user puts something weird as the api_class varaible name?
            _user_class = eval(_user_class)
        else:
            return
            #check if the class in _user_class_str can be found in the user_classes module
        try:
            self.user_class = getattr(api.user_classes, _user_class)()
            self.api_used = True
            self.print_to_log('Found api class {}'.format(_user_class))
        except TypeError:
            self.print_to_log('Could not find class {} in the user_classes folder'.format(_user_class))
            return

        self.user_class.set_state_machine(sm_info)

    def variable_funcs(self, board):
        '''make the variable functions from pycboard availble in the api'''
        if not self.api_used: return
        self.user_class.set_variable = board.set_variable
        #this should maybe not be used as it returns None when framework running
        self.user_class.get_variable = board.get_variable
        self.user_class.print_to_log = self.print_to_log

    def run_start(self, recording):
        if not self.api_used: return
        self.user_class.run_start(recording)
    def run_stop(self):
        if not self.api_used: return
        self.user_class.run_stop()
    def update(self):
        if not self.api_used: return
        self.user_class.update()
    def process_data(self, new_data):
        if not self.api_used: return
        self.user_class.process_data(new_data)

if __name__ == '__main__':
    Api_base()
