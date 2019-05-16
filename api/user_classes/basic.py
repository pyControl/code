from api.api import Api

class Basic(Api):

    def __init__(self):
        '''debugging class for use with blinker_api.py'''
        print('Basic initialised')
        self.updated = False

    def process_data(self, new_data):
        #print(new_data)
        if not self.updated:
            self.set_variable('test_variable_change', 2)
            self.updated = True
