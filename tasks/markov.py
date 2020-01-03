from pyControl.utility import *
import hardware_definition as hw

version = 2019120500 ## YearMonthDayRevision YYYYMMDDrr  can have up to 100 revisions/day

states= [
    'waiting_for_initiation_center',
    'offering_right',
    'offering_left',
    'reject',
    'error',
    'waiting_for_collection_right',
    'waiting_for_collection_left',
    ]

events = [
    'R_nose',
    'C_nose',
    'L_nose',
    'R_lever',
    'L_lever',
    'button',
    'tone_off',
    ]

####### Hidden script variables ##########
v.trial_current_number___ = 0
v.left_presses___ = 0
v.right_presses___ = 0
v.current_tone___ = ''
v.old_tone___ = ''
v.repeats___ = 0
v.outcome___ = 'R'
v.speaker_is_playing___ = False
v.continuous_tone___ = True
v.laser_trial___ = False
v.last_trial_was_laser___ = False

v.reward_probability_set___ = [0.2,0.4,0.6,0.8]
v.time_delay_until_tone_ms___ = 100 

##### Configurable Variables #######
#Left variables
v.reward_probability_left = 1
v.required_presses_left = 1 
v.reward_volume_left = 250 # microliters

#Right variables
v.reward_probability_right = 1
v.required_presses_right = 1
v.reward_volume_right = 250 # microliters

#Other variables
v.speaker_volume = 20 # Speaker volume (range 1 - 30)
v.time_tone_duration_seconds = 1.5 
v.time_reward_available_minutes = 10 # minutes 
v.time_error_freeze_seconds = 1.5 #seconds
v.max_tone_repeats = 1
v.trial_new_block = 0
v.laser_probability = .25
v.laser_with_tone = False
v.laser_with_collection = False

initial_state = 'waiting_for_initiation_center'

def run_start():
    print("Task_Version,{}".format(version))
    for key in v.__dict__.keys():
        print("{},{}".format(key,getattr(v,key))) 
    print("Variables_End,~~~~~")
    hw.Lpump.reset_volume()
    hw.Rpump.reset_volume()
    v.trial_current_number___ = 0
    v.trial_new_block = 0
    hw.Speakers.set_volume(v.speaker_volume)

def waiting_for_initiation_center(event):
    if event == 'entry':
        hw.Cpoke.LED.on()
    elif event == 'C_nose':
        if v.laser_with_collection and v.laser_trial___:
            hw.BaseStation.stop()
        new_trial()

def offering_left(event):
    if event == 'entry':
        v.speaker_is_playing___ = hw.Speakers.play('Left')
        extend_levers()
        if not v.continuous_tone___:
            set_timer('tone_off', v.time_tone_duration_seconds*second,True)
    elif event == 'C_nose': #reject left side
        goto_state('reject')
    elif event == 'L_lever':
        if v.left_presses___==0 and not v.continuous_tone___: # if this is the first lever press and the tone this is not a continuous tone
            stop_tone()
        v.left_presses___ += 1
        if v.left_presses___ == v.required_presses_left:
            goto_state('waiting_for_collection_left')
    elif event == 'R_lever':
        goto_state('error')
    elif event == 'tone_off':
        stop_tone()
    elif event == 'exit':
        retract_levers()

def offering_right(event):
    if event == 'entry':
        v.speaker_is_playing___ = hw.Speakers.play('Right')
        extend_levers()
        if not v.continuous_tone___:
            set_timer('tone_off', v.time_tone_duration_seconds*second,True)
    elif event == 'C_nose': # reject right side
        goto_state('reject')
    elif event == 'L_lever':
        goto_state('error')
    elif event == 'R_lever':
        if v.right_presses___==0 and not v.continuous_tone___: # if this is the first lever press and the tone this isn't a continuous tone
            stop_tone()
        v.right_presses___ +=1
        if v.right_presses___ == v.required_presses_right:
            goto_state('waiting_for_collection_right')
    elif event == 'tone_off':
        stop_tone()
    elif event == 'exit':
        retract_levers()

def reject(event):
    if event == 'entry':
        v.outcome___ = 'R'
        new_trial()

def error(event):
    if event == 'entry':
        hw.Cpoke.LED.off()
        hw.houselight.on()
        v.outcome___ = 'X'
        timed_goto_state('waiting_for_initiation_center',v.time_error_freeze_seconds*second)
    elif event == 'exit':
        hw.houselight.off()

def waiting_for_collection_left(event):
    if event == 'entry':
        timed_goto_state('waiting_for_initiation_center',v.time_reward_available_minutes*minute)
        if withprob(v.reward_probability_left):
            hw.Lpump.infuse(v.reward_volume_left)
            v.outcome___ = 'Y'
    elif event == 'L_nose':
        if v.laser_with_collection and v.laser_trial___:
            hw.BaseStation.trigger()
        goto_state('waiting_for_initiation_center')

def waiting_for_collection_right(event):
    if event == 'entry':
        timed_goto_state('waiting_for_initiation_center',v.time_reward_available_minutes*minute)
        if withprob(v.reward_probability_right):
            hw.Rpump.infuse(v.reward_volume_right)
            v.outcome___ = 'Y'
    elif event == 'R_nose':
        if v.laser_with_collection and v.laser_trial___:
            hw.BaseStation.trigger()
        goto_state('waiting_for_initiation_center')  

def all_states(event):
    if event == 'button':
        hw.Speakers.set_volume(v.speaker_volume)
        print("---------------Speaker Volume is now {}---------------".format(v.speaker_volume))
    Lmsg = hw.Lpump.check_for_serial()
    if Lmsg:
        print("Stopping Framework. Left pump "+Lmsg)
        stop_framework()
    Rmsg = hw.Rpump.check_for_serial()
    if Rmsg:
        print("Stopping framework. Right pump "+Rmsg)
        stop_framework()

def run_end():
    hw.Llever.retract()
    hw.Rlever.retract()
    v.speaker_is_playing___ = hw.Speakers.stop()

################ helper functions ############
def start_new_block ():
    temp_left,temp_right = v.reward_probability_left,v.reward_probability_right 
    while(temp_left == v.reward_probability_left and temp_right == v.reward_probability_right) or (v.reward_probability_left == 0.2 and v.reward_probability_right == 0.2): #make sure the new probabilities aren't identical to current ones. also make sure they're not both 0.2
        v.reward_probability_left = choice(v.reward_probability_set___)
        v.reward_probability_right = choice(v.reward_probability_set___)

    v.trial_new_block = v.trial_current_number___ + int(gauss_rand(300,50))
    print('NB,{},{}'.format(v.trial_current_number___,v.trial_new_block))

def new_trial():
    print('rslt,{},{},{},{},{},{}'.format(v.trial_current_number___,v.reward_probability_left,v.reward_probability_right,v.current_tone___,v.outcome___,v.laser_trial___))
    v.outcome___ = 'N' # reset outcome to not rewarded
    v.trial_current_number___ += 1
    if v.trial_current_number___ >= v.trial_new_block:
        start_new_block()

    if withprob(.5):
        new_tone = 'L'
    else:
        new_tone = 'R'

    # check that maximum repeats haven't been exceeded
    if new_tone == v.old_tone___:
        v.repeats___ += 1
        if v.repeats___ > v.max_tone_repeats:
            v.repeats___ = 0
            if new_tone == 'L':
                new_tone = 'R'
            else:
                new_tone = 'L'
    else:
        v.repeats___ = 0

    v.old_tone___ = v.current_tone___ = new_tone

    # determine if laser trial or not
    v.last_trial_was_laser___ = v.laser_trial___
    if v.laser_with_collection or v.laser_with_tone:
        v.laser_trial___ = withprob(v.laser_probability)
    else:
        v.laser_trial___ = False

    if v.laser_trial___ and v.laser_with_tone:
        if not v.last_trial_was_laser___:
            hw.BaseStation.trigger()
        else:
            print('prevent double laser')
            v.laser_trial___ = False
    if v.current_tone___ == 'L':
        timed_goto_state('offering_left',v.time_delay_until_tone_ms___)
    else:
        timed_goto_state('offering_right',v.time_delay_until_tone_ms___)

def extend_levers():
    hw.Cpoke.LED.on()
    hw.Llever.extend()
    hw.Rlever.extend()
    v.right_presses___ = 0
    v.left_presses___ = 0

def retract_levers():
    hw.Llever.retract()
    hw.Rlever.retract()    
    stop_tone()
    hw.Cpoke.LED.off()

def stop_tone():
    if v.speaker_is_playing___:
        v.speaker_is_playing___ = hw.Speakers.stop()
        disarm_timer('tone_off')
        if v.laser_with_tone and v.laser_trial___:
            hw.BaseStation.stop()