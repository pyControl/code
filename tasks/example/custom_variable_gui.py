# A demonstration of using a custom variable dialog
# Does not require any hardware except micropython board.
# The onboard LED will alternate between red and green at a specified frequency
# Either color can be enabled or disabled using checkboxes
# The frequency can be adjusted between 0.2 and 30 Hz, using the spin box

from pyControl.utility import *
from devices import *
from pyb import LED

red_LED = LED(1)
green_LED = LED(2)

# States and events.
states = ['green_off','green_on','red_off','red_on']
events = []

initial_state = 'red_on'

# Variables 
v.green_enabled = True
v.red_enabled = True
v.blink_rate = 8 #Hz
v.blink_counts = [3,1] # red, green

v.current_count___ = 0

# Use custom variable GUI that is defined in gui/user_variable_GUIs/blink_gui.py
v.variable_gui = 'my_custom_gui' 

# Define behaviour. 
def red_on(event):
    if event == 'entry':
        v.current_count___ += 1
        timed_goto_state('red_off', 1.0/v.blink_rate * second)
        if v.red_enabled:
            red_LED.on()

def red_off(event):
    if event == 'entry':
        red_LED.off()
        if v.current_count___ < v.blink_counts[0]:
            timed_goto_state('red_on', 1.0/v.blink_rate * second)
        else:
            timed_goto_state('green_on', 1.0/v.blink_rate * second)
            v.current_count___ = 0

def green_on(event):
    if event == 'entry':
        v.current_count___ += 1
        timed_goto_state('green_off', 1.0/v.blink_rate * second)
        if v.green_enabled:
            green_LED.on()

def green_off(event):
    if event == 'entry':
        green_LED.off()
        if v.current_count___ < v.blink_counts[1]:
            timed_goto_state('green_on', 1.0/v.blink_rate * second)
        else:
            timed_goto_state('red_on', 1.0/v.blink_rate * second)
            v.current_count___ = 0


def run_end():  # Turn off hardware at end of run.
    red_LED.off()
    green_LED.off()