
# state machine which flashes the blue LED on the pyboard on and off.
# and calls the api
# Does not require any hardware except micropython board.

from pyControl.utility import *

# States and events.

states = ['LED_on',
          'LED_off']
events = []

initial_state = 'LED_off'

# Variables.

v.LED_n  = 4 # Number of LED to use.

#should change up to 2 if api is working correctly
v.test_variable_change = 1
v.api_class = 'Basic'
# Define behaviour.

def LED_on(event):
    if event == 'entry':
        #should print 2 if api correct
        print(v.test_variable_change)
        timed_goto_state('LED_off', 0.5 * second)
        pyb.LED(v.LED_n).on()
    elif event == 'exit':
        pyb.LED(v.LED_n).off()

def LED_off(event):
    if event == 'entry':
        timed_goto_state('LED_on', 0.5 * second)

def run_end():  # Turn off hardware at end of run.
    pyb.LED(v.LED_n).off()
