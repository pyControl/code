from pyControl import *
import examples as ex

fw.verbose = True  # Set human readable output.

example = 'two_step'  # blinker, button or two_step,

if example == 'blinker':
    task = sm.State_machine(ex.blinker)           # Initialise state machine.

elif example == 'button':
    poke = hw.Poke(1, 'button_event', debounce = 200) # Initialise hardware.
    task = sm.State_machine(ex.button, poke)          # Initialise state machine.

elif example == 'two_step':  
    box = hw.Box()                               # Initialise hardware.
    task = sm.State_machine(ex.two_step, box)    # Initialise state machine.

def run(dur = 20):  # Run pyControl.
    fw.run(dur)  







from pyControl import *
import examples as ex
fw.verbose = True
box = hw.Box()                               # Initialise hardware.
task = sm.State_machine(ex.two_step, box)    # Initialise state machine.