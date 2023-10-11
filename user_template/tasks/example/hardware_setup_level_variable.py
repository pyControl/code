# An example task that grabs a value from a setup's hardware variables
# Does not require any hardware except micropython board.
# Any variable beginning with "v.hw_" is treated as a hardware variable
# Hardware variables can be assigned values by going to the setups tab, selecting a named setup, and clicking the "variables" button to bring up the hardware variables dialog
# A hardware variable must first be added to a task file before it will be available for editing in the hardware variables dialog

from pyControl.utility import *

# States and events.
states = ["print_msg"]
events = ["timer_done"]

initial_state = "print_msg"

# Hardware setup level variables

v.hw_solenoid = None  # this value is just a placeholder and will be overwritten when the task is loaded


# State behaviour functions


def print_msg(event):
    if event == "entry":
        set_timer("timer_done", 1 * second, output_event=False)
    elif event == "timer_done":
        print('This task is using a hardware setup level variable equal to "{}"'.format(v.hw_solenoid))
        set_timer("timer_done", 1 * second, output_event=False)
