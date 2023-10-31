# Example user class that can be used as an interface between the computer and
# the state machine running on the pyboard.
# This class can respond to states, events, prints, variable changes, and analog data
# This file will be running on your desktop computer and can therefore be used
# for heavy processing or to interact with programs outside of PyControl GUI using
# whatever Python libraries you'd like.


import random
from source.gui.api import Api


# This class should be have the same name as the file and inherit the API class
# look at gui/api.py to see what functions can be redefined and called
class Example_user_class(Api):
    def __init__(self):
        self.off_count = 0

    # this runs at the start of sessoin
    def run_start(self):
        self.print_to_log("\nYou can print directly to the log from user class")

    # use this function
    def process_data_user(self, data):
        # check if state changed to LED_off
        LED_off_happened = [state.name == "LED_off" for state in data["states"]]
        if LED_off_happened:
            self.off_count += 1
            new_duration = random.triangular(0.1, 1, 5.5)
            self.set_variable("LED_duration", round(new_duration, 3))
            if self.off_count % 4 == 0:
                self.trigger_event("event_a")

        # check for print message from task
        msgs_from_task = [printed.data.split("=")[1] for printed in data["prints"] if "vals_from_task=" in printed.data]
        for msg in msgs_from_task:
            x, y, z = msg.split(",")
            total = int(x) + int(y) + int(z)
            self.print_message("{} and {} and {} total to {}".format(x, y, z, total))

    def run_start(self):
        self.print_to_log("\nMessage from config/user_classes/Example_user_class.py at the start of the run")

    def run_stop(self):
        self.print_to_log("\nMessage from config/user_classes/Example_user_class.py at the end of the run")
