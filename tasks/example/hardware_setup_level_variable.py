# A simple state machine which flashes the blue LED on the pyboard on and off.
# Does not require any hardware except micropython board.

from pyControl.utility import *
from devices import *

# States and events.
states = ["print_msg"]
events = ["timer_done"]

initial_state = "print_msg"

# Hardware specific variables
v.hw_solenoid = None  # this value is just a placeholder and will be overwritten when the task is loaded


# Define behaviour.
def print_msg(event):
    if event == "entry":
        set_timer("timer_done", 1 * second, output_event=False)
    elif event == "timer_done":
        print(f'This task is using a hardware setup level variable equal to "{v.hw_solenoid}"')
        set_timer("timer_done", 1 * second, output_event=False)
