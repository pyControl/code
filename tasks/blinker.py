# A simple state machine which flashes the blue LED on the pyboard on and off.
# Does not require any hardware except micropython board.

from pyControl.utility import *

# States and events.

states = ['LED_on',
          'LED_off']

events = []

initial_state = 'LED_off'

# Variables.

v.LED_n  = 4 # Number of LED to use.


# Define behaviour. 

def LED_on(event):
    if event == 'entry':
        pyb.LED(v.LED_n).on()
    elif event == 'exit':
        pyb.LED(v.LED_n).off()

def LED_off(event):
    if event == 'entry':
        timed_goto_state('LED_on', 0.5 * second)

def run_end():  # Turn off hardware at end of run.
    pyb.LED(v.LED_n).off()



