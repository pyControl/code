# A script for testing the hardware, optionally run by the cli.run_experiment() before running the experiment
# so the user can check the hardware is all working as expected.

from pyControl.utility import *
import hardware_definition as hw

# States and events.

states = ['init_state',
          'left_active',
          'right_active',
          'left_release',
          'right_release']

events = ['left_poke', 
          'right_poke',
          'center_poke',
          'center_poke_out']

initial_state = 'init_state'

# Run start and stop behaviour.

def run_start():  # 
    hw.houselight.on()

def run_end():  
    hw.off()

# State & event dependent behaviour.

def init_state(event):
    # Select left or right poke.
    if event == 'entry':
        hw.center_poke.LED.on()
    elif event == 'exit':
        hw.center_poke.LED.off()
    elif event == 'left_poke':
        goto('left_active')
    elif event == 'right_poke':
        goto('right_active')

def left_active(event):
    # Poke center to trigger solenoid or right to goto right_active.
    if event == 'entry':
        hw.left_poke.LED.on()
    elif event == 'exit':
        hw.left_poke.LED.off()
    elif event == 'center_poke':
        goto('left_release')
    elif event == 'right_poke':
        goto('right_active')

def right_active(event):
    # Poke center to trigger solenoid or left to goto left_active.
    if event == 'entry':
        hw.right_poke.LED.on()
    elif event == 'exit':
        hw.right_poke.LED.off()
    elif event == 'left_poke':
        goto('left_active')
    elif event == 'center_poke':
        goto('right_release')

def left_release(event):
    # Trigger left solenoid while center poke IR beam remains broken.
    if event == 'entry':
        hw.left_poke.SOL.on()
    elif event == 'exit':
        hw.left_poke.SOL.off()
    elif event == 'center_poke_out':
        goto('left_active')
    elif event == 'right_poke':
        goto('right_active')

def right_release(event):
    # Trigger right solenoid while center poke IR beam remains broken.
    if event == 'entry':
        hw.right_poke.SOL.on()
    elif event == 'exit':
        hw.right_poke.SOL.off()
    elif event == 'left_poke':
        goto('left_active')
    elif event == 'center_poke_out':
        goto('right_active')
