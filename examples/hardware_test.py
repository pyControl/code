from pyControl.utility import *

# States and events.

states = ['init_state',
          'left_active',
          'right_active',
          'left_release',
          'right_release']

events = ['left_poke', 
          'left_poke_out',
          'right_poke',
          'right_poke_out',
          'high_poke',
          'high_poke_out',
          'low_poke',
          'low_poke_out']

initial_state = 'init_state'

# Run start and stop behaviour.

def run_start():  # 
    hw.houselight.on()
    hw.house_red.on()

def run_end():  
    hw.off()

# State & event dependent behaviour.

def init_state(event):
    if event == 'entry':
        hw.center_poke.LED.on()
    elif event == 'exit':
        hw.center_poke.LED.off()
    elif event == 'left_poke':
        goto('left_active')
    elif event == 'right_poke':
        goto('right_active')

def left_active(event):
    if event == 'entry':
        hw.left_poke.LED.on()
    elif event == 'exit':
        hw.left_poke.LED.off()
    elif event == 'high_poke':
        goto('left_release')
    elif event == 'right_poke':
        goto('right_active')

def right_active(event):
    if event == 'entry':
        hw.right_poke.LED.on()
    elif event == 'exit':
        hw.right_poke.LED.off()
    elif event == 'left_poke':
        goto('left_active')
    elif event == 'low_poke':
        goto('right_release')

def left_release(event):
    if event == 'entry':
        hw.left_poke.SOL.on()
    elif event == 'exit':
        hw.left_poke.SOL.off()
    elif event == 'high_poke_out':
        goto('left_active')
    elif event == 'right_poke':
        goto('right_active')

def right_release(event):
    if event == 'entry':
        hw.right_poke.SOL.on()
    elif event == 'exit':
        hw.right_poke.SOL.off()
    elif event == 'left_poke':
        goto('left_active')
    elif event == 'low_poke_out':
        goto('right_active')
