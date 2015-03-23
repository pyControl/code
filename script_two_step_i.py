import pyControl as pc
import state_machine_j as sm
import hardware as hw
import examples.two_step_i as two_step_i
from utility import *

pc.verbose = True  # Set human readable output.

box = hw.Box(pc)   # Initialise hardware.

task = sm.State_machine(pc, two_step_i, box)  # Initialise task.

def run(dur = 20):  # Run PyControl.
	pc.run_machines(dur * second)  







