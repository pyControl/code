import pyControl as pc
import state_machine as sm
import hardware as hw
import examples as ex
from utility import *

pc.verbose = True  # Set human readable output.

example = 'two_step'  # blinker, button or two_step,

if example == 'blinker':
	task = sm.State_machine(pc, ex.blinker)           # Initialise state machine.

elif example == 'button':
	poke = hw.Poke(pc, 1, 'button_event') # Initialise hardware.
	task = sm.State_machine(pc, ex.button, poke)   # Initialise state machine.

elif example == 'two_step':  
	box = hw.Box(pc)                               # Initialise hardware.
	task = sm.State_machine(pc, ex.two_step, box)  # # Initialise state machine.


def run(dur = 20):  # Run pyControl.
	pc.run_machines(dur * second)  







