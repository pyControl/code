# Example of how the all_states function can be used to make things happen in parallel
# with the state set of a task.  The states cycle the red, green and yellow LEDs on
# when the usr pushbutton on the pyboard is pressed.  In parallel the blue LED is
# flashed on and off using the all_states function and timer events.

# Does not require any hardware except a micropython board.

from pyControl.utility import *
from devices import *

# Define hardware (normally done in seperate hardware definition file).

pyboard_button = Digital_input("X17", falling_event="button_press", pull="up")  # USR button on pyboard.

blue_LED = Digital_output("B4")
red_LED = Digital_output("A13")
green_LED = Digital_output("A14")
yellow_LED = Digital_output("A15")

# States and events.

states = [
    "red_on",
    "green_on",
    "yellow_on",
]

events = [
    "button_press",
    "blue_on",
    "blue_off",
]

initial_state = "red_on"

# Run start behaviour.


def run_start():
    # Turn on blue LED and set timer to turn it off in 1 second.
    blue_LED.on()
    set_timer("blue_off", 1 * second, output_event=True)


# State behaviour functions.


def red_on(event):
    # Red LED on, button press transitions to green_on state.
    if event == "entry":
        red_LED.on()
    elif event == "exit":
        red_LED.off()
    elif event == "button_press":
        goto_state("green_on")


def green_on(event):
    # Green LED on, button press transitions to yellow_on state.
    if event == "entry":
        green_LED.on()
    elif event == "exit":
        green_LED.off()
    elif event == "button_press":
        goto_state("yellow_on")


def yellow_on(event):
    # Yellow LED on, button press transitions to red_on state.
    if event == "entry":
        yellow_LED.on()
    elif event == "exit":
        yellow_LED.off()
    elif event == "button_press":
        goto_state("red_on")


# State independent behaviour.


def all_states(event):
    # Turn blue LED on and off when the corrsponding timer trigger, set timer for next blue on/off.
    if event == "blue_on":
        blue_LED.on()
        set_timer("blue_off", 1 * second, output_event=True)
    elif event == "blue_off":
        blue_LED.off()
        set_timer("blue_on", 1 * second, output_event=True)


# Run end behaviour.


def run_end():
    # Turn off LEDs at end of run.
    for LED in [blue_LED, red_LED, green_LED, yellow_LED]:
        LED.off()
