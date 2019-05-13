from pyControl.utility import *
import hardware_definition as hw
from devices import *


#### States and events.
# --------------------------------------------------------------------------------------

states = [ 'trial_start', 'light_pulse', 'detect_lick_go', 'detect_lick_nogo', 'lick_withold', 'ITI', 'earned_reward', 'auto_reward']
        
events = ['autoreward', 'lick_window', 'pulse_end','lick_1', 'solenoidOff', 'pyb_button']

initial_state = 'lick_withold'

###### set this to True if the animal should be started in the passive phase. False if should be started in active
v.autoreward = False
## ---------------------------------------------------------------------------------------------------------------
###### set this as the current inedex the mouse should be started at
v.LED_steps = 0 #the number of LED steps down, index of v.LED_currents to use
## ---------------------------------------------------------------------------------------------------------------


# calculate from linear regression of power meter results
v.LED_currents = [64.73, 32.43, 13.05, 6.59, 3.36, 1.42, 0.78]

##### set the parameters of the task here
## --------------------------------------------------------------------------------------

# autoreward parameters
v.consec_autoswitch = 3 #the number of consecutive earned rewards during autoreward phase to swtich to active phase 

# session parameters
v.reward_time = 60 # time that the solenoid is open during rewards (ms)
v.d_prime_threshold = 2

# trial parameters
if v.autoreward:
    v.chanceGo = 0.7 # chance of a go trial
else:
    v.chanceGo = 0.5 
    
v.lick_window = 2.5  # reward time window during which mouse has to lick (s)


# inter-trial-interval parameters
v.withold_len = [x / 10 for x in range(40, 61)] #time that the animal must withold licking, a list in 0.1 increments from 4-6, that can be sampled randomly
v.ITI = 5 # the inter-trial interval(S). This is also the time during which rewards are registered as recieved if the animal licks

# parameters for swtiching between autorewarded and not autorewarded conditions
v.miss_switch = 3 # the number of consecutive missed trials before the animal is switched back to autoreward

# the number of consecutive trials where the animal did not drink a reward before ending the framework
v.end_ignore = 10

v.pulse_len = 20 #length of the LED pulse (ms)
v.num_pulses = 5 #number of LED pulses

v.rolling_window_len = 10 #the length of the rolling d' window


##### initialise global task variables
# --------------------------------------------------------------------------------------

# general task counters
v.num_trials = 0 # count trials
v.num_rewards = 0 # the number of rewards delivered
v.num_ignored = 0
v.consecIgnored = 0 #the number of rewards that have been delieverd that the animal has not drunk
#v.rolling_counter = 0 #counts to 10 trials on a rolling basis

# counters for go and nogo trials
v.num_go = 0 # the total number of go trials
v.num_nogo = 0
v.consecGo = 0 # count the number of consecutive go and nogo trials
v.consecNoGo = 0

# trial outcome counters
v.rolling_hit = [] # rolling hit counter
v.num_misses = 0
v.num_rejections = 0
v.rolling_fa = [] #rolling fa counter

v.d_prime = 0

v.consecMiss = 0 #counts misses on not autorewarded trials

# reward counters
v.num_rewards_received = 0 # how many rewards the mouse has successfully recieved
v.reward_increment = True #whether to increment rewards. Stops multiple increments from mulitple licks
v.gave_reward = False #tell the ITI function whether a reward has just been delivered
v.drank_reward = False #whether the animal drank its reward

# autoreward task variables
v.num_autorewards = 0 #the number of times the animal has been autorewarded in one autoreward session
v.num_earned_rewards = 0 # how many times the mouse licks before autoreward arrives
v.consec_autocorrect  = 0 #how many consective earned rewards during autoreward

v.boost_autoreward = False # whether to give a boost autoreward after a few consecutive misses
v.num_boosts = 0 #the number of boost phases
v.num_boost_autorewards = 0

v.hit_rate = 'NaN'
v.false_alarm_rate = 'NaN'

v.pulses_done = 0 # the number of pulses of the LED

#misc variables
v.print_switch = True #print the switch between autoreward conditions only once
 
v.plotted_variables = []

# Run start and stop behaviour.
def run_start():
    ##make sure solenoid is shut before starting 
    hw.solenoid.off()

def run_end():  
    hw.solenoid.off()
    hw.LED.off()# Turn off hardware outputs.

def lick_withold(event):
    if event == 'entry':
        length = choice(v.withold_len) 
        print('must withold licking for %s seconds' %length)
        timed_goto_state('trial_start', length*second)
    if event == 'lick_1':
        goto_state('lick_withold')
      
         
def trial_start(event):

    # randomly choose whether it's a go or nogo trial
    if event == 'entry':
        v.num_trials += 1
        v.isGo = withprob(v.chanceGo)
        
        if v.isGo:
            v.isNoGo = False
        else:
            v.isNoGo = True

        #allow the mouse to again increment rewards recieved
        v.reward_increment = True

        # do not have more than 3 consecutive go or nogo trials
        if v.consecNoGo == 3 or v.isGo and v.consecGo < 3:

            print('goTrial')
            v.isGo = True
            v.isNoGo = False

            v.num_go += 1
        
            v.consecGo += 1
            v.consecNoGo = 0

            # the pyboard needs a few ms to process this function
            timed_goto_state('light_pulse',5*ms)
                          
        elif v.consecGo == 3 or v.isNoGo and v.consecNoGo < 3:
            
            print('nogo_trial')
            v.num_nogo += 1

            v.isGo = False
            v.isNoGo = True

            v.consecNoGo += 1
            v.consecGo = 0
            
            # the pyboard needs a few ms to process this function
            timed_goto_state('detect_lick_nogo', 5*ms)
     


def light_pulse(event):

    if event == 'entry': 

        # start the clock, timing the lick window
        set_timer('lick_window', v.lick_window * second)

        # takes 200ms to do pulses, so switch state after 200ms. this has to be an event so can disarm it if lick
        set_timer('pulse_end', v.pulse_len*ms)
      
        hw.LED.on(LED_current_mA=v.LED_currents[v.LED_steps])
 

    if event == 'pulse_end':
        hw.LED.off()    
        v.pulses_done += 1
        #continue pulsing the LED
        if v.pulses_done != v.num_pulses:
            timed_goto_state('light_pulse', 15*ms)
        else:
            v.pulses_done = 0
            timed_goto_state('detect_lick_go', 50*ms)
            

    if event == 'lick_1':

        # wait until pulsing has finished before switching state
        timed_goto_state('earned_reward', timer_remaining('pulse_end')*ms)
        hw.LED.off()
        disarm_timer('lick_window')
        disarm_timer('pulse_end') 


def detect_lick_go(event):

    if event == 'lick_1':
      
        disarm_timer('lick_window')
        v.boost_autoreward = False
        # the pyboard needs a few ms to process this function
        timed_goto_state('earned_reward', 5*ms)

    if event == 'lick_window':
        
        #the mouse has failed to lick in the window
        v.rolling_hit.append(0)
        print('missed trial')
        if not v.autoreward:
            v.consecMiss += 1 #do not count misses during initial autoreward phase
        if v.autoreward or v.boost_autoreward:
            goto_state('auto_reward')
        else:
            goto_state('ITI')


def detect_lick_nogo(event):

    if event == 'entry':
    # the timer is set here to keep go and nogo trials the same length
        set_timer('lick_window', v.lick_window * second)

    if event == 'lick_1':
        v.rolling_fa.append(1)
        disarm_timer('lick_window')
        print('false positive trial')
        # the pyboard needs a few ms to process this function
        timed_goto_state('ITI', 10*ms)

    if event == 'lick_window':
        v.rolling_fa.append(0)
        print('correct rejection') 
        goto_state('ITI')


    
def earned_reward(event):

    if event == 'entry':
        v.consecMiss = 0
        hw.solenoid.on()
        set_timer('solenoidOff', v.reward_time*ms)
        print('earned_reward')
        print('waterON')
        v.gave_reward = True
        v.rolling_hit.append(1)
        v.num_rewards += 1
        v.num_earned_rewards += 1
        
        if v.autoreward:
            v.consec_autocorrect += 1
            print('correct before autoreward')           
            
        elif v.boost_autoreward:
            print('correct before boost autoreward')
            v.boost_autoreward = False

    if event == 'solenoidOff':
        hw.solenoid.off()
        goto_state('ITI')


def auto_reward(event):

    if event == 'entry':
        hw.solenoid.on()
        set_timer('solenoidOff', v.reward_time*ms)
        
        v.consec_autocorrect = 0
  
        v.num_rewards += 1
        v.gave_reward = True
        print('deliver autoreward')
        print('waterON')
        
        if v.autoreward:
            v.num_autorewards += 1
        if v.boost_autoreward:
            v.num_boost_autorewards += 1

    if event == 'solenoidOff':
        goto_state('ITI') 
        hw.solenoid.off()


def ITI(event):

    if event == 'entry':
        #keep the d' calculation rolling with a length of v.rolling_window_len
        if len(v.rolling_hit) > v.rolling_window_len:
            del v.rolling_hit[0]
        if len(v.rolling_fa) > v.rolling_window_len:
            del v.rolling_fa[0]
            
        #this is necessary for a learned mouse with 0 fas.
        if sum(v.rolling_fa) == 0 and len(v.rolling_fa) > 2:
            v.rolling_fa.append(0.0001)
            
        try:
            v.hit_rate = sum(v.rolling_hit) / len(v.rolling_hit)
            v.false_alarm_rate = sum(v.rolling_fa) / len(v.rolling_fa)
            v.d_prime = d_prime(v.hit_rate, v.false_alarm_rate)
        except:
            print('division by zero error')
            
        

        
        #print useful general information about task state
        print('the mouse has done %s trials total'%v.num_trials)
        print('d_prime is %s'%v.d_prime) 
        print('hit_rate is %s'%v.hit_rate)
        print('fa_rate is %s'%v.false_alarm_rate)
        print('the mouse has missed %s consecutive trials' %v.consecMiss)
        print('the mouse has ignored %s consecutive rewards'%v.consecIgnored)
       
        print('LED current is %s'%v.LED_currents[v.LED_steps])


            
        if v.autoreward:
            print('correct licks during autoreward phase: %s '%v.num_earned_rewards)
            print('consecutive correct autorewards is: %s ' %v.consec_autocorrect)
        else:
            print('total number rewards is %s'%v.num_rewards)
            
            
        timed_goto_state('lick_withold', v.ITI*second)

    #criteria to switch out of autoreward
    if v.consec_autocorrect == v.consec_autoswitch:
        v.consec_autocorrect = 0
        v.autoreward = False
        v.chanceGo = 0.5

        #reset the task
        v.num_go = 0
        v.num_nogo = 0
        v.rolling_hit = []
        v.rolling_fa = []
        v.num_misses = 0
        v.num_rejections = 0
        v.d_prime = 0

        print('switching out of autoreward')
            

    # criteria to switch to boostautoreward
    if v.consecMiss == v.miss_switch and not v.autoreward:
        v.boost_autoreward = True
        v.num_boosts += 1
        v.consecMiss = 0
        print('giving a boost autoreward on the next go trial')

    # criteria to change LED current
    if not v.autoreward and v.d_prime > v.d_prime_threshold:
        #mouse needs to have done at least 7 trials at this LED power
        if v.num_go+v.num_nogo > 7:
            print('Changing LED current')
            v.LED_steps += 1
            print('LED current is now %s'%v.LED_currents[v.LED_steps])           
            v.num_go = 0
            v.num_nogo = 0
            v.rolling_hit = []
            v.rolling_fa = []
            v.num_misses = 0
            v.num_rejections = 0
            v.d_prime = 0
            
            if v.LED_steps == len(v.LED_currents):
                print('mouse has completed task to lowest power level')
                stop_framework()

    if v.consecIgnored > v.end_ignore or v.num_boosts == 20:
        
        if not v.autoreward:
            print('ending task due to boredom or fault')
            stop_framework()

    # increment the reward recieved counter once if mouse licks the reward
    # this will not be registered if the animal licks only in the reward states
    # but normally it takes a few seconds to drink

    if event == 'lick_1' and v.isGo and v.reward_increment and v.gave_reward:
        print('reward received')
        v.num_rewards_received += 1
        v.reward_increment = False
        v.consecIgnored = 0
        v.drank_reward = True

        if v.boost_autoreward:
            #stop autorewarding if the animal drinks
            v.boost_autoreward = False
            v.consecMiss = 0 #dont increment on drank boost autorewards
            
    if event == 'exit':
        if not v.drank_reward and v.gave_reward:
            v.num_ignored += 1
            v.consecIgnored += 1
            print(v.consecIgnored)
            
        #ensure this is set to false for the next trial
        v.gave_reward = False
        v.drank_reward = False

def all_states(event):

    if event == 'lick_1':
        print('lick')

    

    
    
     



