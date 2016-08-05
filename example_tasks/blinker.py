from pyControl.utility import *

# States and events.

states = {'LED_on'  :  1,
          'LED_off' :  2}

events = {'timer_evt' :  3}

initial_state = 'LED_off'

# Variables.

v.LED_n  = 1 # Number of LED to use.
        
# Define behaviour.

def LED_on(event):
    if event == 'entry':
        set_timer('timer_evt', 0.5 * second)
        pyb.LED(v.LED_n).on()
    elif event == 'exit':
        pyb.LED(v.LED_n).off()
    elif event == 'timer_evt':
        goto('LED_off')

def LED_off(event):
    if event == 'entry':
        set_timer('timer_evt', 0.5 * second)
    elif event == 'timer_evt':
        goto('LED_on')

def run_end():  # Turn off hardware at end of run.
    pyb.LED(v.LED_n).off()


