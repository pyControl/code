# A simple state machine which turns the blue LED on the pyboard on and off when the usr pushbutton
# on the pyboard is pressed.  Does not require any hardware except micropython board.

from pyControl.utility import *
from devices import Digital_input

# Define hardware (normally done in seperate hardware definition file).

pyboard_button = Digital_input('X17', falling_event='button_press', pull='up')  # USR button on pyboard.

# States and events.
  
states= ['LED_on',
         'LED_off']

events = ['button_press']

initial_state = 'LED_off'

# Define behaviour.

def LED_on(event):
        if event == 'entry':
            pyb.LED(4).on()
        elif event == 'exit':
            pyb.LED(4).off()
        elif event == 'button_press':
            goto_state('LED_off')

def LED_off(event):
        if event == 'button_press':
            goto_state('LED_on')

def run_end():  # Turn off hardware at end of run.
    pyb.LED(4).off()

