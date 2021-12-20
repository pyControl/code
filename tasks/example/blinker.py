# A simple state machine which flashes the blue LED on the pyboard on and off.
# Does not require any hardware except micropython board.

from pyControl.utility import *
from devices import *

# Define hardware (normally done in seperate hardware definition file).

blue_LED = Digital_output('B4')

# States and events.

states = ['LED_on',
          'LED_off']

events = []

initial_state = 'LED_off'
        
# Define behaviour. 

def LED_on(event):
    if event == 'entry':
        timed_goto_state('LED_off', 0.5 * second)
        blue_LED.on()
    elif event == 'exit':
        blue_LED.off()

def LED_off(event):
    if event == 'entry':
        timed_goto_state('LED_on', 0.5 * second)

def run_end():  # Turn off hardware at end of run.
    blue_LED.off()