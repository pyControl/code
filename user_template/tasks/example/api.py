# An example task that uses an API class to communicate with a python script running on the desktop computer.

from pyControl.utility import *
from devices import *
from pyb import LED

# Define hardware (normally done in seperate hardware definition file).

green_LED = LED(2)

# States and events.
states = [
    "LED_on",
    "LED_off",
]
events = ["event_a"]

initial_state = "LED_on"

# Variables
v.blink_count = 0
v.LED_duration = 0.5
v.api_class = "Example_user_class"  # class being run is found at config/user_classes/Example_user_class.py


# State behaviour functions
def LED_on(event):
    if event == "entry":
        timed_goto_state("LED_off", v.LED_duration * second)
        green_LED.on()
        v.blink_count += 1
        if v.blink_count > 5:
            v.blink_count = 0
            x, y, z = randint(1, 10), randint(1, 30), randint(-8, 9)
            print("vals_from_task={},{},{}".format(x, y, z))  # print can be used to send data to the user class
    elif event == "exit":
        green_LED.off()


def LED_off(event):
    if event == "entry":
        timed_goto_state("LED_on", v.LED_duration * second)


# State independent behaviour.
def all_states(event):
    if event == "event_a":
        print("this will print every 3 blinks")


# Run end behaviour
def run_end():  # Turn off hardware at end of run.
    green_LED.off()
