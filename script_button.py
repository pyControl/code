import pyControl as pc
import hardware as hw
from examples.button import *

pc.verbose = True  # Set human readable output.

# Initialise hardware.

boxIO = hw.BoxIO(pc)

poke_1 = hw.Poke(boxIO, 1, 'button_event')
poke_2 = hw.Poke(boxIO, 2, 'button_event')
poke_3 = hw.Poke(boxIO, 3, 'button_event')
poke_4 = hw.Poke(boxIO, 4, 'button_event')

# # Instantiate state machines.

button_1 = Button(pc, poke_1)
button_2 = Button(pc, poke_2)
button_3 = Button(pc, poke_3)
button_4 = Button(pc, poke_4)

# Run PyControl.

def run(dur = 20):
	pc.run_machines(dur * second)  







