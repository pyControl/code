from pyControl.utility import *

# States and events.

states = ['LED_on',
          'LED_off']

events = []

initial_state = 'LED_off'

# Variables.

v.LED_n  = 1 # Number of LED to use.
        
# Define behaviour. 

def LED_on(event):
    if event == 'entry':
        timed_goto('LED_off', 0.5 * second)
        pyb.LED(v.LED_n).on()
    elif event == 'exit':
        pyb.LED(v.LED_n).off()

def LED_off(event):
    if event == 'entry':
        timed_goto('LED_on', 0.5 * second)

def run_end():  # Turn off hardware at end of run.
    pyb.LED(v.LED_n).off()



