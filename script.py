import PyControl as pc
from examples import *

# Instantiate state machines.

blinker_1 = blinker(pc, LED = 1, period = 1)      
blinker_2 = blinker(pc, LED = 2, period = 0.5)     
blinker_3 = blinker(pc, LED = 3, period = 0.25) 
blinker_4 = blinker(pc, LED = 4, period = 0.125) 

# Run PyControl.
pc.run_machines(5 * second)  







