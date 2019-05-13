# task to turn both the board LED and the analog LED driver at the same time

from pyControl.utility import *
import hardware_definition as hw
# States and events.

states = ['sol_on',
		  'sol_off']

events = []

initial_state = 'sol_on'

# Variables.

v.open_time = 60 #solenoid opening time (ms)	
v.tot_openings = 200 #task will stop after this number of openings
v.delay = 20 #time solenoid is closed 

v.num_openings = 0 #count the number of openings completed	
        

def sol_on(event):

    if event == 'entry':
        hw.solenoid.on()
        timed_goto_state('sol_off', v.open_time * ms)

    if event == 'exit':
        hw.solenoid.off()

def sol_off(event):
    if event == 'entry':
        v.num_openings += 1
        timed_goto_state('sol_on', v.delay * ms)
        

def all_states(event):
    if v.num_openings == v.tot_openings:
        stop_framework()
        
        

    


