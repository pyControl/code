from pyControl.utility import *
import hardware_definition as hw
from devices import *
import pyb
board = Breakout_1_2()

states = ['lick_withold', 'trial_start', 'SLM_state', 'LED_state', 'detect_lick_go', 'detect_lick_nogo', 'ITI', 'auto_reward', 'earned_reward']
        
events = ['SLM_trial', 'LED_trial', 'lick_window', 'lick_1', 'solenoidOff', 'autoreward', 'rsync']

initial_state = 'lick_withold'



##### set the parameters of the task here
## --------------------------------------------------------------------------------------

# session parameters
v.reward_time = 60 # time that the solenoid is open during rewards (ms)
v.d_prime_threshold = 2
 
v.lick_window = 0.01  # reward time window during which mouse has to lick (s)

# inter-trial-interval parameters
v.withold_len = [x / 1000 for x in range(40, 61)] #time that the animal must withold licking, a list in 0.1 increments from 4-6, that can be sampled randomly
v.ITI = 2 # the inter-trial interval(S). This is also the time during which rewards are registered as recieved if the animal licks


v.total_SLM = 300
# parameters for switching between autorewarded and not autorewarded conditions
v.miss_switch = 3000 # the number of consecutive missed trials before the animal is switched back to autoreward

# the number of consecutive trials where the animal did not drink a reward before ending the framework
v.end_ignore = 3000

v.rolling_window_len = 10 #the length of the rolling d' window


##### initialise global task variables
# --------------------------------------------------------------------------------------

# general task counters
v.num_trials = 0 # count trials
v.num_rewards = 0 # the number of rewards delivered
v.num_ignored = 0 #the number of rewards that have been delieverd that the animal has not drunk
v.consecIgnored = 0 

# counters for go and nogo trials
v.num_SLM = 0 # the total number of SLM trials

# the current trial state
v.isSLM = False
v.isLED = False
v.isNoGo = False

# trial outcome counters
v.num_misses = 0
v.num_rejections = 0

v.rolling_hit = [] # rolling hit counter
v.rolling_fa = [] #rolling fa counter
v.d_prime = 0

v.consecMiss = 0 #counts misses on not autorewarded trials

# reward counters
v.num_rewards_received = 0 # how many rewards the mouse has successfully recieved
v.reward_increment = True #whether to increment rewards. Stops multiple increments from mulitple licks
v.gave_reward = False #tell the ITI function whether a reward has just been delivered
v.drank_reward = False #whether the animal drank its reward

#autoreward settings
v.autoreward = False #this is currently not used
v.boost_autoreward = False # whether to give a boost autoreward after a few consecutive misses
v.num_boosts = 0 #the number of boost phases


v.hit_rate = 'NaN'
v.false_alarm_rate = 'NaN'


#misc variables
v.print_switch = True #print the switch between autoreward conditions only once
 
# Run start and stop behaviour.
def run_start():
    ##make sure solenoid is shut before starting 
    hw.solenoid.off()

def run_end():  
    hw.solenoid.off()
    print('mouse has recieved {} rewards total'.format(v.num_rewards_received))
 

def threeway_probtree(P, recurs=False):
    
    '''
    returns three mutually exclusive booleans with probabilty P of each occuring
    i.e P(bool1) = P, P(bool2) = P, P(bool3) = P 
    recurs if you want to try again if all three bools are False (effectively setting P=1/3)
    in current state all bools must have same P but can be changed if required (JR 2019)
    '''
    
    assert 3*P < 1
    
    p1 = P
    if withprob(p1): return (True, False, False)

    p2 =  P/(1-P)
    if withprob(p2): return (False, True, False)

    p3 = P / ((1-P) * (1-(P/(1-P))))
    if withprob(p3): return (False, False, True)

    if recurs: 
        return threeway_probtree(P, recurs=True)
    else:     
        return (False, False, False)


#### task code starts here
#######################################################
 
def lick_withold(event):
    if event == 'entry':
        length = choice(v.withold_len) 
        print('must withold licking for %s seconds' %length)
        timed_goto_state('trial_start', length*second)
    if event == 'lick_1':
        goto_state('lick_withold')

def trial_start(event):

    # randomly choose whether it's an LED, SLM or nogo trial
    # I have not yet implemented consecutive trial number checks but should happen rarely as three trial types 
    if event == 'entry':
        v.num_trials += 1
    
        print('num_SLM is {}'.format(v.num_SLM))
        timed_goto_state('SLM_state', 100*ms)      

       

def SLM_state(event):    
    if event == 'entry':  
        
        

        
        #call the blimp all optical stim function
        publish_event('SLM_trial')
        trial_barcode = (gauss_rand(1000,1000))
        print('Trigger SLM trial Number {0} Barcode {1}'.format(v.num_SLM, trial_barcode))
            
        timed_goto_state('detect_lick_go', 10*ms)
        
        
        v.num_SLM+=1
        
      
def detect_lick_go(event):

    if event == 'entry':
        # start the clock, timing the lick window
        set_timer('lick_window', v.lick_window * second)
    
    if event == 'lick_1':          
        # the pyboard needs a few ms to process this function
        timed_goto_state('earned_reward', 5*ms)
        disarm_timer('lick_window')
        v.boost_autoreward = False
        print('correct trial')
 
    if event == 'lick_window':       
        #the mouse has failed to lick in the window 
        v.rolling_hit.append(0)
        v.consecMiss += 1 #do not count misses during initial autoreward phase
        print('missed trial')
        
        if v.boost_autoreward:
            goto_state('auto_reward')
        else:
            goto_state('ITI')
            
def detect_lick_nogo(event):

    if event == 'entry':
        set_timer('lick_window', v.lick_window * second)
        
    if event == 'lick_1':
        v.rolling_fa.append(1)
        disarm_timer('lick_window')
        # the pyboard needs a few ms to process this function
        timed_goto_state('ITI', 10*ms)
        
    if event == 'lick_window':
        v.rolling_fa.append(0)
        print('correct rejection') 
        goto_state('ITI')
        
        

def earned_reward(event):

    if event == 'entry':
        v.consecMiss = 0
      
        v.gave_reward = True
        v.rolling_hit.append(1)
        v.num_rewards += 1
       
        if v.boost_autoreward:
            v.boost_autoreward = False
        
        hw.solenoid.on()  
        print('waterON')
        set_timer('solenoidOff', v.reward_time*ms)
        
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


        # criteria to switch to boostautoreward
        if v.consecMiss == v.miss_switch and not v.autoreward:
            v.boost_autoreward = True
            v.num_boosts += 1
            v.consecMiss = 0
            print('giving a boost autoreward on the next go trial')
            
        if v.consecIgnored > v.end_ignore or v.num_boosts == 200:
            print('ending task due to boredom or fault')
            stop_framework()
            
        timed_goto_state('lick_withold', v.ITI*second)  
      
    # increment the reward recieved counter once if mouse licks the reward
    # this will not be registered if the animal licks only in the reward states
    # but normally it takes a few seconds to drink
    
    #shitty hack 
    if v.isSLM or v.isLED: 
        isGo = True
    else:
        isGo = False
    
    if event == 'lick_1' and isGo and v.reward_increment and v.gave_reward:
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

            
        #ensure this is set to false for the next trial
        v.gave_reward = False
        v.drank_reward = False
        
def all_states(event):
    if v.num_SLM == v.total_SLM:
        stop_framework()
        
        
        
        
        
