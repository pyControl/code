import random
from gui.api import Api


# This class should be have the same name as the file and inherit the API class
class Blinker(Api):
    # API for the Blinker class demonstrating setting variables functionality.
    def __init__(self):
        self.i = 0

    def process_data_user(self, data):
        # do something when a particular state transition happens
        LED_off_happened = any([state.name == "LED_off" for state in data["states"]])
        if LED_off_happened:
            new_duration = round(random.triangular(0.5, 1.5, 4), 3)
            self.set_variable("LED_duration", new_duration)
