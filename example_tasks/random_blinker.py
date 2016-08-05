from pyControl.utility import *

# States and events.

states = {'LED_on': 1, 'LED_off': 2}

events = {'timer_evt': 3}

initial_state = 'LED_on'

# Variables.

v.LED_n = 1  # Number of LED to use.
v.time_dur = 10

# Define behaviour.

def LED_on(event):
    if event == 'entry':
        set_timer('timer_evt', v.time_dur * second)
        pyb.LED(v.LED_n).on()
    elif event == 'exit':
        pyb.LED(v.LED_n).off()
    elif event == 'timer_evt':
        goto('LED_off')


def LED_off(event):
    if event == 'entry':
        set_timer('timer_evt', v.time_dur * second)
    elif event == 'timer_evt':
        goto('LED_on')


def run_end():  # Turn off hardware at end of run.
    v.time_dur = int(random() * 10)
    pyb.LED(v.LED_n).off()
