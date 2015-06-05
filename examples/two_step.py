from pyControl.utility import *

# States and events.

states = ['pre_session',
          'post_session',
          'center_active',
          'left_active',
          'right_active',
          'left_reward',
          'right_reward',
          'wait_for_poke_out',
          'inter_trial']

events = ['left_poke', 
          'left_poke_out',
          'right_poke',
          'right_poke_out',
          'high_poke',
          'low_poke',
          'session_timer',
          'state_timer',
          'session_startstop']

initial_state = 'pre_session'

# Variables.

v.norm_prob = 0.8
v.reward_probs = [0.2,0.8]

# Run start and stop behaviour.

def run_end():  # Turn off hardware at end of run.
    hw.off()

# State & event dependent behaviour.

def pre_session(event):
    if event == 'session_startstop':
        hw.houselight.on()
        goto('center_active')

def post_session(event):
    if event == 'entry':
        hw.houselight.off()     

def center_active(event):
    if event == 'entry':
        hw.center_poke.LED.on()
    elif event == 'exit':
        hw.center_poke.LED.off()
    elif event == 'high_poke':
        if withprob(v.norm_prob):
            goto('left_active')
        else:
            goto('right_active')
    elif event == 'low_poke':
        if withprob(v.norm_prob):
            goto('right_active')
        else:
            goto('left_active')

def left_active(event):
    if event == 'entry':
        hw.left_poke.LED.on()
    elif event == 'exit':
        hw.left_poke.LED.off()
    elif event == 'left_poke':
        if withprob(v.reward_probs[0]):
            goto('left_reward')
        else:
            goto('wait_for_poke_out')

def right_active(event):
    if event == 'entry':
        hw.right_poke.LED.on()
    elif event == 'exit':
        hw.right_poke.LED.off()
    elif event == 'right_poke':
        if withprob(v.reward_probs[1]):
            goto('right_reward')
        else:
            goto('wait_for_poke_out')

def left_reward(event):
    if event == 'entry':
        hw.left_poke.SOL.on()
        set_timer('state_timer', 100 * ms)
    elif event == 'exit':
        hw.left_poke.SOL.off()
    elif event == 'state_timer':
        goto('wait_for_poke_out')

def right_reward(event):
    if event == 'entry':
        hw.right_poke.SOL.on()
        set_timer('state_timer', 100 * ms)
    if event == 'exit':
        hw.right_poke.SOL.off()
    if event == 'state_timer':
        goto('wait_for_poke_out')     
    
def wait_for_poke_out(event):
    if event == 'entry':
        if not (hw.left_poke.value() or \
                hw.right_poke.value()):
            goto('inter_trial') # Subject already left poke.
    elif event in ['left_poke_out', 'right_poke_out']:
        goto('inter_trial')

def inter_trial(event):
    if event == 'entry':
        set_timer('state_timer', 1 * second)
    if event == 'state_timer':
        goto('center_active')

def all_states(event):
    if event == 'session_startstop' and not state == 'pre_session':
        goto('post_session')










