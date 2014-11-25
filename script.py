import PyControl as pc
import hardware as hw
from examples import *


# Initialise hardware.

boxIO = hw.BoxIO(pc)
poke = hw.Poke(boxIO, 1, rising_event = 1)

# Instantiate state machines.

#blinker_1 = Blinker(pc, LED = 1, period = 1)      
#blinker_2 = Blinker(pc, LED = 2, period = 0.5)     

button_1 = Button(pc)


# Run PyControl.
pc.run_machines(20 * second)  







