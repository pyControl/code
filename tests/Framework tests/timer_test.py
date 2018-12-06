# Task for testing that the timer functions are working OK.  Blue, green
# and yellow LEDs should flash synchronously at 1Hz, red LED should not 
# illuminate.

from pyControl.utility import *
from devices import *

# Hardaware

blue_LED   = Digital_output('B4')
red_LED    = Digital_output('A13')
green_LED  = Digital_output('A14')
yellow_LED = Digital_output('A15')

# States and events.

states = ['blue_off',
          'blue_on',
          'red_on']

events = ['blue_timer',
          'green_timer',
          'red_timer',
          'pause_timer',
          'unpause_timer',
          'disarm_timer',
          'yellow_timer',
          'unused_timer']

initial_state = 'blue_on'

# Variables.

        
# Define behaviour. 

def run_start():
    green_LED.on()
    yellow_LED.on()
    set_timer('green_timer', 0.2*second)
    set_timer('pause_timer', 0.1*second)
    set_timer('yellow_timer', 0.5*second)

def blue_on(event):
    if event == 'entry':
        timed_goto_state('blue_off', 0.5*second)
        blue_LED.on()
    elif event == 'exit':
        blue_LED.off()

def blue_off(event):
    if event == 'entry':
        set_timer('blue_timer', 0.5*second)
        timed_goto_state('red_on', 0.6*second)
    elif event == 'blue_timer':
        goto_state('blue_on')

def red_on(event):
    if event == 'entry':
        red_LED.on()

def all_states(event):
    if event == 'green_timer':
        set_timer('green_timer', 0.2*second, output_event=True)
        set_timer('pause_timer', 0.1*second)
        set_timer('red_timer', 50*ms)
        set_timer('disarm_timer', 40*ms)
        green_LED.toggle()
    elif event == 'pause_timer':
        pause_timer('green_timer')
        set_timer('unpause_timer', 0.3*second)
    elif event == 'unpause_timer':
        unpause_timer('green_timer')
        print('Timer remaining  : {}'.format(timer_remaining('green_timer')))
        print('Not set remaining: {}'.format(timer_remaining('unused_timer')))
    elif event == 'red_timer':
        goto_state('red_on')
    elif event == 'disarm_timer':
        disarm_timer('red_timer')
    elif event == 'yellow_timer':
        reset_timer('yellow_timer', 0.5*second)
        set_timer('yellow_timer', 0.75*second)
        yellow_LED.toggle()



