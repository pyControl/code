# A simple state machine which flashes the blue LED on the pyboard on and off.
# Does not require any hardware except micropython board.

from pyControl.utility import *
from devices import *
from pyb import LED

# Define hardware (normally done in seperate hardware definition file).
green_LED = LED(2)

# States and events.
states = ["LED_on", "LED_off"]
events = ["event_from_user_class"]
initial_state = "LED_on"

# Variables
v.blink_count = 0
v.LED_duration = 0.5
v.api_class = "Example"


# Define behaviour.
def LED_on(event):
    if event == "entry":
        timed_goto_state("LED_off", v.LED_duration * second)
        green_LED.on()
        v.blink_count+=1
        if v.blink_count>5:
            v.blink_count=0
            # a print statement can be used to send data to the user class
            print("random,{},{},{}".format(randint(1,10),randint(1,30),randint(-8,9)))
    elif event == "exit":
        green_LED.off()


def LED_off(event):
    if event == "entry":
        timed_goto_state("LED_on", v.LED_duration * second)

def all_states(event):
    if event == "event_from_user_class":
        print("this will print every 2 blinks")



def run_end():  # Turn off hardware at end of run.
    green_LED.off()
