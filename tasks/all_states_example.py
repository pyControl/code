# Example of how the all_states function can be used to make things happen in parallel
# with the state set of a task.  The states cycle the red, green and yellow LEDs on
# when the usr pushbutton on the pyboard is pressed.  In parallel the blue LED is 
# flashed on and off using the all_states function and timer events.

# Does not require any hardware except a micropython board.

from pyControl.utility import *
from devices import *

# Define hardware (normally done in seperate hardware definition file).

pyboard_button = Digital_input('X17', falling_event='button_press', pull='up')  # USR button on pyboard.

# States and events.
  
states= ['red_on',
         'green_on',
         'yellow_on']

events = ['button_press',
          'blue_on',
          'blue_off']

initial_state = 'red_on'

# Run start behaviour.

def run_start():
    # Turn on blue LED and set timer to turn it off in 1 second.
    pyb.LED(4).on()
    set_timer('blue_off', 1*second, output_event=True)

# State behaviour functions.

def red_on(event):
    # Red LED on, button press transitions to green_on state.
    if event == 'entry':
        pyb.LED(1).on()
    elif event == 'exit':
        pyb.LED(1).off()
    elif event == 'button_press':
        goto_state('green_on')

def green_on(event):
    # Green LED on, button press transitions to yellow_on state.
    if event == 'entry':
        pyb.LED(2).on()
    elif event == 'exit':
        pyb.LED(2).off()
    elif event == 'button_press':
        goto_state('yellow_on')

def yellow_on(event):
    # Yellow LED on, button press transitions to red_on state.
    if event == 'entry':
        pyb.LED(3).on()
    elif event == 'exit':
        pyb.LED(3).off()
    elif event == 'button_press':
        goto_state('red_on')

# State independent behaviour.

def all_states(event):
    # Turn blue LED on and off when the corrsponding timer trigger, set timer for next blue on/off.
    if event == 'blue_on':
        pyb.LED(4).on()
        set_timer('blue_off', 1*second, output_event=True)
    elif event == 'blue_off':
        pyb.LED(4).off()
        set_timer('blue_on' , 1*second, output_event=True)

# Run end behaviour.

def run_end():
    # Turn off LEDs at end of run.
    for i in range(4):
        pyb.LED(i+1).off()