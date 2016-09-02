from pyControl.utility import *

#-------------------------------------------------------------------------------------
# Outcome generator.
#-------------------------------------------------------------------------------------

class Outcome_generator:

    def __init__(self, verbose = False):
        # Parameters
        self.verbose = verbose # Display user readable output.

        self.state = {'trans' : withprob(0.5),          # True for A blocks, false for B blocks.
                      'reward': int(withprob(0.5)) * 2} # 0 for left good, 1 for neutral, 2 for right good.

        self.settings = {'first_session'       :  False,
                         'high_trans_contrast' :  True,
                         'high_reward_contrast':  True}

        self.threshold = 0.75 
        self.tau = 8.  # Time constant of moving average.
        self.min_block_length = 40       # Minimum block length.
        self.min_trials_post_criterion = 20  # Number of trials after transition criterion reached before transtion occurs.
        self.mean_neutral_block_length = 50
        self.first_session_rewards = 40 # Number of trials in first session which automatically recieve reward.

        self.mov_ave = exp_mov_ave(tau = self.tau, init_value = 0.5)   # Moving average of agents choices.


    def reset(self):

        if self.settings['high_trans_contrast']:
            self.norm_prob    = 0.9 # Probability of normal transition.
        else: # Low transition contrast.
            self.norm_prob    = 0.8 # Probability of normal transition.

        if self.settings['high_reward_contrast']:
            self.reward_probs = [[0.9, 0.1],  # Reward probabilities in each reward block type.
                                 [0.4, 0.4],
                                 [0.1, 0.9]]    
        else: # Low reward contrast.
            self.reward_probs = [[0.8, 0.2],  # Reward probabilities in each reward block type.
                                 [0.4, 0.4],
                                 [0.2, 0.8]]

        print(self.settings)

        self.mov_ave.reset()
        self.block_trials = 0                       # Number of trials into current block.
        self.trial_number = 0                       # Current trial number.
        self.reward_number = 0                      # Current number of rewards.
        self.block_number = 0                       # Current block number.
        self.trans_crit_reached = False             # True if transition criterion reached in current block.
        self.trials_post_criterion = 0              # Current number of trials past criterion.    
        self.nb_hazard_prob = 1 / (self.mean_neutral_block_length # Prob. of block transition on each trial
                                   - self.min_block_length)       # after min block length in neutral blocks.
        
    def first_step(self, first_step_choice):
        # Update moving average.
        self.mov_ave.update(first_step_choice)
        second_step_state = first_step_choice ^  withprob(self.norm_prob) ^ self.state['trans']
        if self.verbose: self.print_state()
        return second_step_state
        
    def second_step(self, second_step_state):
        # Evaluate trial outcome.

        self.block_trials += 1
        self.trial_number += 1

        if (self.settings['first_session'] and # First trials of first session are all rewarded.
            self.trial_number <= self.first_session_rewards):
            outcome = True
        else:
            outcome = withprob(self.reward_probs[self.state['reward']][second_step_state])
        
        if outcome:
            self.reward_number += 1
        
        if self.trans_crit_reached:
            self.trials_post_criterion +=1
        elif (self.state['reward'] != 1):  # Non-neutral block - check for threshold crossing.
            if (((self.state['trans'] == (self.state['reward'] == 0)) # High is good option..
                and (self.mov_ave.ave > self.threshold))              # ..and high treshold crossed.              
            or ((self.state['trans'] != (self.state['reward'] == 0))  # or Low is good option..
                and (self.mov_ave.ave < (1. - self.threshold)))):     # .. and low threshold crossed.
                    self.trans_crit_reached = True
                    print('# Transition criterion reached.')

        # Check for block transition.
        if ((self.block_trials >= self.min_block_length) and                     # Transitions only occur after min block length trials..
             ((self.state['reward'] == 1 and withprob(self.nb_hazard_prob)) or   # Neutral block: transitions are stochastic.
              (self.trials_post_criterion >= self.min_trials_post_criterion))):  # Non-neutral block: transitions occur fixed
             # Block transition                                                  # number of trials after threshold crossing.
            self.block_number += 1
            self.block_trials  = 0
            self.trials_post_criterion = 0
            self.trans_crit_reached = False
            if self.state['reward'] == 1:                 # End of neutral block always transitions to one side 
                self.state['reward'] = 2 * withprob(0.5)  # being good without reversal of transition probabilities.
            else: # End of block with one side good, 50% chance of change in transition probs.
                if withprob(0.5): #Reversal in transition probabilities.
                    self.state['trans'] = not self.state['trans']
                    if withprob(0.5): # 50% chance of transition to neutral block.
                        self.state['reward'] = 1
                else: # No reversal in transition probabilities.
                    if withprob(0.5):
                        self.state['reward'] = 1 # Transition to neutral block.
                    else:
                        self.state['reward'] = 2 - self.state['reward'] # Invert reward probs.
            self.print_block_info()
        
        return outcome


    def print_state(self):
        print('# Trial number: {}, Reward number: {}, Moving ave: {}'            
             .format(self.trial_number, self.reward_number, self.mov_ave.ave))

    def print_block_info(self):
        print('-1 {} {}'.format(self.state['reward'], int(self.state['trans'])))
        if self.verbose:
            print('# Reward block    : ' + {0:'0 - Left good', 
                                            1:'1 - Neutral', 
                                            2:'2 - Right good'}[self.state['reward']])
            print('# Transition block: ' + {0:'B - High --> right', 
                                            1:'A - High --> left'}[self.state['trans']])

    def print_summary(self):
        print('$ Total trials    : {}'.format(self.trial_number))
        print('$ Total rewards   : {}'.format(self.reward_number))
        print('$ Completed blocks: {}'.format(self.block_number))

#-------------------------------------------------------------------------------------
# State machine definition.
#-------------------------------------------------------------------------------------

# States and events.

states = ['center_active',
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
          'session_timer']

initial_state = 'center_active'

# Variables.

v.session_duration = 1.5 * hour
v.inter_trial_interval = 1 * second
v.reward_delivery_durations = [80, 80] # ms
v.outcome_generator = Outcome_generator(verbose = True)

# Run start and stop behaviour.

def run_start():
    hw.houselight.on()
    set_timer('session_timer', v.session_duration)
    print('Reward sizes: ' + repr(v.reward_delivery_durations))
    v.outcome_generator.reset()
    v.outcome_generator.print_block_info()
    

def run_end():  
    hw.off() # Turn off hardware outputs.
    v.outcome_generator.print_summary()

# State & event dependent behaviour.    

def center_active(event):
    if event == 'entry':
        hw.center_poke.LED.on()
    elif event == 'exit':
        hw.center_poke.LED.off()
    elif event == 'high_poke':
        if v.outcome_generator.first_step(True):
            goto('left_active')
        else:
            goto('right_active')
    elif event == 'low_poke':
        if v.outcome_generator.first_step(False):
            goto('left_active')
        else:
            goto('right_active')


def left_active(event):
    if event == 'entry':
        hw.left_poke.LED.on()
    elif event == 'exit':
        hw.left_poke.LED.off()
    elif event == 'left_poke':
        if v.outcome_generator.second_step(False):
            goto('left_reward')
        else:
            goto('wait_for_poke_out')

def right_active(event):
    if event == 'entry':
        hw.right_poke.LED.on()
    elif event == 'exit':
        hw.right_poke.LED.off()
    elif event == 'right_poke':
        if v.outcome_generator.second_step(True):
            goto('right_reward')
        else:
            goto('wait_for_poke_out')

def left_reward(event):
    if event == 'entry':
        hw.left_poke.SOL.on()
        set_timer('state_timer', v.reward_delivery_durations[0])
    elif event == 'exit':
        hw.left_poke.SOL.off()
    elif event == 'state_timer':
        goto('wait_for_poke_out')

def right_reward(event):
    if event == 'entry':
        hw.right_poke.SOL.on()
        set_timer('state_timer', v.reward_delivery_durations[1])
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
        set_timer('state_timer', v.inter_trial_interval)
    if event == 'state_timer':
        goto('center_active')

def all_states(event):
    if event == 'session_timer':
        stop_framework() # End session










