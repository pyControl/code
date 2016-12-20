# A probabilistic reversal learning task in which the subject must initiate
# the trial in the center poke, then chose left or right for a probabilistic
# reward.  The reward probabilities on the left and right side reverse from
# time to time.

from pyControl.utility import *
import hardware_definition as hw

#-------------------------------------------------------------------------
# States and events.
#-------------------------------------------------------------------------

states = ['init_trial',
          'choice_state',
          'left_reward',
          'right_reward',
          'inter_trial_interval']

events = ['left_poke',
          'center_poke',
          'right_poke',
          'session_timer']

initial_state = 'init_trial'

#-------------------------------------------------------------------------
# Variables.
#-------------------------------------------------------------------------

v.session_duration = 1*hour
v.reward_durations = [100,100] # Reward delivery duration (ms) [left, right]
v.ITI_duration = 1*second # Inter trial interval duration.
v.n_rewards = 0 # Number of rewards obtained.
v.n_trials = 0 # Number of trials recieved.
v.mean_block_length = 10 # Average block length between reversals.
v.state = withprob(0.5) # Which side is currently good: True: left, False: right
v.good_prob = 0.8 # Reward probabilities on the good side.
v.bad_prob  = 0.2 # Reward probabilities on the bad side.

#-------------------------------------------------------------------------        
# Define behaviour.
#-------------------------------------------------------------------------

# Run start and stop behaviour.

def run_start(): 
    # Set session timer and turn on houslight.
    set_timer('session_timer', v.session_duration)  
    hw.houselight.on()                             
    
def run_end():
    # Turn off all hardware outputs.  
    hw.off()

# State behaviour functions.

def init_trial(event):
    # Turn on center Poke LED and wait for center poke.
    if event == 'entry':
        hw.center_poke.LED.on()
    elif event == 'exit':
        hw.center_poke.LED.off()
    elif event == 'center_poke':
        goto_state('choice_state')

def choice_state(event):
    # Wait for left or right choice and evaluate if reward is delivered.
    if event == 'entry':
        print('Trials: {}, Rewards:  {}'.format(v.n_trials, v.n_rewards))
        hw.left_poke.LED.on()
        hw.right_poke.LED.on()
    elif event == 'exit':
        hw.left_poke.LED.off()
        hw.right_poke.LED.off()
    elif event == 'left_poke':
        if ((v.state and withprob(v.good_prob)) or (not v.state and withprob(v.bad_prob))):
            goto_state('left_reward')
        else:
            goto_state('inter_trial_interval')
    elif event == 'right_poke':
        if ((not v.state and withprob(v.good_prob)) or (v.state and withprob(v.bad_prob))):
            goto_state('right_reward')
        else:
            goto_state('inter_trial_interval')

def left_reward(event):
    # Deliver reward to left poke, increment reward counter.
    if event == 'entry':
        timed_goto_state('inter_trial_interval', v.reward_durations[0])
        hw.left_poke.SOL.on()
        v.n_rewards += 1
    elif event == 'exit':
        hw.left_poke.SOL.off()

def right_reward(event):
    # Deliver reward to right poke, increment reward counter.
    if event == 'entry':
        timed_goto_state('inter_trial_interval', v.reward_durations[1])
        hw.right_poke.SOL.on()
        v.n_rewards += 1
    elif event == 'exit':
        hw.right_poke.SOL.off()

def inter_trial_interval(event):
    # Increment trial counter, check for reversal transition.
    if event == 'entry':
        timed_goto_state('init_trial', v.ITI_duration)
        v.n_trials += 1
        if withprob(1/v.mean_block_length): 
            print('Block transition')
            v.state = not v.state # Reversal has occured.

# State independent behaviour.

def all_states(event):
    # When 'session_timer' event occurs stop framework to end session.
    if event == 'session_timer':
        stop_framework()