# Test for analog and digital inputs.  The blue LED should be on when the usr
# button is pressed and the green LED should be on when the voltage on pin
# X1 is above ~1.5V.

from pyControl.utility import *
from devices import *

# Define hardware (normally done in seperate hardware definition file).

pyboard_button = Digital_input(
    "X17", rising_event="button_release", falling_event="button_press", pull="up"  # USR button on pyboard.
)

analog_input = Analog_input(
    "X1", "Analog", 1000, threshold=2000, rising_event="rising_edge", falling_event="falling_edge"
)

blue_LED = Digital_output("B4")
green_LED = Digital_output("A14")

# States and events.

states = ["LED_on", "LED_off"]

events = ["button_press", "button_release", "rising_edge", "falling_edge"]

initial_state = "LED_off"

# Define behaviour.


def run_start():
    analog_input.record()


def LED_on(event):
    if event == "entry":
        blue_LED.on()
    elif event == "exit":
        blue_LED.off()
    elif event == "button_release":
        goto_state("LED_off")


def LED_off(event):
    if event == "button_press":
        goto_state("LED_on")


def all_states(event):
    if event == "rising_edge":
        green_LED.on()
    elif event == "falling_edge":
        green_LED.off()
