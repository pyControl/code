import pyControl as pc
import hardware as hw
from examples.two_step import *

pc.verbose = True  # Set human readable output.

box = hw.Box(pc)   # Initialise hardware.

task = Two_step(pc,box)  # Initialise task.

def run(dur = 20):  # Run PyControl.
	pc.run_machines(dur * second)  







