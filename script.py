from PyControl import *
from examples import *

# Instantiate state machines.

blinker_1 = blinker(LED = 1, period = 1)      
blinker_2 = blinker(LED = 2, period = 0.5)     
blinker_3 = blinker(LED = 3, period = 0.25) 
blinker_4 = blinker(LED = 4, period = 0.125) 

# Register machiness with PyControl.
register([blinker_1, blinker_2, blinker_3, blinker_4]) 


# Run PyControl.
run_machines(5 * second)  







