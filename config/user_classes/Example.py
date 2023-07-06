# Example user class that can be used as an interface between the computer and
# the state machine  running on the pyboard.
# This class can respond to states, events, prints, variable changes, and analog data
# This file will be running on your desktop computer and can therefore be used
# for heavy processing or to interact with programs outside of PyControl GUI using
# whatever Python libraries you'd like


import random
from gui.api import Api


# This class should be have the same name as the file and inherit the API class
class Example(Api):
    def __init__(self):
        self.off_count = 0

    # this runs at the start of sessoin
    def run_start(self):
        self.print_to_log("\nYou can print directly to the log from user class")

    def process_data_user(self, data):
        # check if state changed to LED_off
        LED_off_happened = any([state.name == "LED_off" for state in data["states"]])
        if LED_off_happened:
            self.off_count += 1
            new_duration = random.triangular(0.1, 1, 2.5)
            self.set_variable("LED_duration", round(new_duration, 3))
            if self.off_count % 2 == 0:
                self.trigger_event("event_from_user_class")

        # check for trial summary message
        msg_from_task = [printed.data for printed in data["prints"] if "random" in printed.data]
        if msg_from_task:
            _, x, y, z = msg_from_task[0].split(",")
            total = int(x) + int(y) + int(z)
            self.print_to_log("{} and {} and {} total to {}".format(x, y, z, total))
