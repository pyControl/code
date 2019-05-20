from api.api import Api

class Blinker(Api):
    # API for the Blinker class demonstrating setting variables functionality.
        
    def __init__(self):
        self.i = 0

    def process_data(self, new_data):
        for nd in new_data:
            if nd[0] == 'D' and self.ID2name[nd[2]] == 'LED_off': 
                self.i = (self.i + 1) % 4
                self.set_variable('LED_n', self.i+1)

