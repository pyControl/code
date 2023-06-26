# A simple state machine which flashes the blue LED on the pyboard on and off.
# Does not require any hardware except micropython board.

from pyControl.utility import *
from devices import *
from pyb import LED

# Define hardware (normally done in seperate hardware definition file).
green_LED = LED(2)

# States and events.
states = ["LED_on", "LED_off"]
events = []
initial_state = "LED_on"

# variables
v.LED_duration = 0.5
# v.api_class = 'Blinker' # Uncomment to use Blinker API example.

# Define behaviour.
def LED_on(event):
    if event == "entry":
        timed_goto_state("LED_off", v.LED_duration * second)
        green_LED.on()
    elif event == "exit":
        green_LED.off()


def LED_off(event):
    if event == "entry":
        timed_goto_state("LED_on", v.LED_duration * second)


def run_end():  # Turn off hardware at end of run.
    green_LED.off()
