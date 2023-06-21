# A simple state machine which turns the blue LED on the pyboard on for 1
# second when the usr pushbutton on the pyboard or 
# the button in the Controls GUI is pressed three times.
# Does not require any hardware except a micropython board.

from pyControl.utility import *
from devices import *

# Define hardware
button = Digital_input("X17", rising_event="button_press", pull="up")  # pyboard usr button.
LED = Digital_output("B4")

# States and events.
states = ["LED_on", "LED_off"]
initial_state = "LED_off"

events = ["button_press", "gui_press"]

# Variables
v.press_n___ = 0  # private variable (ends with ___) will not appear in GUI
v.threshold = 3  # LED will turn on once this threshold is met/exceeded
v.btn_press = "gui_press"  #  event that we want to publish when GUI button is pressed


# State behaviour functions.
def LED_off(event):
    if event in ("button_press", "gui_press"):
        v.press_n___ = v.press_n___ + 1
        print("Press number {}".format(v.press_n___))
        if v.press_n___ >= v.threshold:
            goto_state("LED_on")


def LED_on(event):
    if event == "entry":
        LED.on()
        timed_goto_state("LED_off", 1 * second)
        v.press_n___ = 0
    elif event == "exit":
        LED.off()
