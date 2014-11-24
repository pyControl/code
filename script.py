import PyControl as pc
import hardware as hw
from examples import *

# Initialise hardware.

box_IO = hw.Box_IO()
poke = hw.Poke(box_IO, 1, rising_event = 1)

# Instantiate state machines.

#blinker_1 = blinker(pc, LED = 1, period = 1)      
#blinker_2 = blinker(pc, LED = 2, period = 0.5)     

button_1 = button(pc)


# Run PyControl.
pc.run_machines(5 * second)  







