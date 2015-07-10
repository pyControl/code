from pyControl.utility import *

# States and events.

states = ['wait_for_poke',
          'left_release',
          'left_pause',
          'right_release',
          'right_pause']

events = ['left_poke', 
          'right_poke',
          'high_poke',
          'low_poke',
          'state_timer']

initial_state = 'wait_for_poke'

# Variables.

v.n_release = 50
v.del_dur  = 80
v.n = 1
v.IRI = 200

# Run start and stop behaviour.

def run_start():  # 
    hw.houselight.on()

def run_end():  
    hw.off()

# State & event dependent behaviour.


def wait_for_poke(event):
    if event == 'entry':
        hw.center_poke.LED.on()
        v.n = 0
    elif event == 'exit':
        hw.center_poke.LED.off()
    elif event == 'high_poke':
        goto('left_release')
    elif event == 'low_poke':
        goto('right_release')

def left_release(event):
    if event == 'entry':
        v.n +=1
        set_timer('state_timer', v.del_dur)
        hw.left_poke.LED.on()
        hw.left_poke.SOL.on()
    elif event == 'exit':
        hw.left_poke.LED.off()
        hw.left_poke.SOL.off()
    elif event == 'state_timer':
        if v.n >= v.n_release:
            goto('wait_for_poke')
        else:
            goto('left_pause')

def left_pause(event):
    if event == 'entry':
        set_timer('state_timer', v.IRI)
    if event == 'state_timer':
        goto('left_release')


def right_release(event):
    if event == 'entry':
        v.n +=1
        set_timer('state_timer', v.del_dur)
        hw.right_poke.LED.on()
        hw.right_poke.SOL.on()        
    elif event == 'exit':
        hw.right_poke.LED.off()
        hw.right_poke.SOL.off()
    elif event == 'state_timer':
        if v.n >= v.n_release:
            goto('wait_for_poke')
        else:
            goto('right_pause')

def right_pause(event):
    if event == 'entry':
        set_timer('state_timer', v.IRI)
    if event == 'state_timer':
        goto('right_release')

