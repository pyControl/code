from pyControl.utility import *

# States and events.
  
states= ['LED_on',
         'LED_off']

events = ['button_event']

initial_state = 'LED_off'

# Define behaviour.

def LED_on(event):
        if event == 'entry':
            hw.LED.on()
        elif event == 'exit':
            hw.LED.off()
        elif event == 'button_event':
            goto('LED_off')

def LED_off(event):
        if event == 'button_event':
            goto('LED_on')

def run_end():  # Turn off hardware at end of run.
    hw.LED.off()

