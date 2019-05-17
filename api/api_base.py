from importlib import import_module

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
        if not 'api_class' in sm_info['variables']:
            return # Task does not use API.
        
        API_name = eval(sm_info['variables']['api_class'])
        # Try to import and instantiate the user API.
        try:
            user_module_name = 'api.user_classes.{}'.format(API_name)
            user_module = import_module(user_module_name)
        except ModuleNotFoundError:
            self.print_to_log('\nCould not find module: {}'.format(user_module_name))
            return
        if not hasattr(user_module, API_name):
            self.print_to_log('\nCould not find class "{}" in {}'
                .format(API_name, user_module_name))
        self.user_class = getattr(user_module, API_name)()
        self.api_used = True
        self.print_to_log('\nFound api class {}'.format(API_name))
        
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
