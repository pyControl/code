from utility import *

# States and events.

states = {'LED_on'  :  1,
          'LED_off' :  2}

events = {'timer_evt' :  3}

initial_state = 'LED_off'

# Variables.

v.LED = pyb.LED(1)
v.period = 1
        
# Define behaviour.

def LED_on(event):
    if event == 'entry':
        set_timer('timer_evt', v.period * second)
        v.LED.on()
    elif event == 'exit':
        v.LED.off()
    elif event == 'timer_evt':
        goto('LED_off')

def LED_off(event):
    if event == 'entry':
        set_timer('timer_evt', v.period * second)
    elif event == 'timer_evt':
        goto('LED_on')

def run_end():  # Turn off hardware at end of run.
    v.LED.off()



