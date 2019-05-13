# task to turn both the board LED and the analog LED driver at the same time

from pyControl.utility import *
import hardware_definition as hw
# States and events.

states = ['LED_on',
		  'LED_off']

events = []

initial_state = 'LED_on'

# Variables.

v.on_time = 5000 
v.off_time = 500 


v.LED_current = 400








def LED_on(event):

    if event == 'entry':
        hw.LED.on(LED_current_mA=v.LED_current)
        timed_goto_state('LED_off', v.on_time * ms)

    if event == 'exit':
        hw.LED.off()

def LED_off(event):
    if event == 'entry':
        timed_goto_state('LED_on', v.off_time * ms)
        
def run_end():
    hw.LED.off()
        
        

    


