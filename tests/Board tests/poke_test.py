# Connect breakout board 1.2 to the computer, plug in the 12V power supply.  
# Connect a Poke to port 3 of the breakout board. When you break the IR beam of 
# the Poke the LED and solenoid will turn on.

from pyControl.utility import *
from devices import Breakout_1_2, Poke

# Define hardware

board = Breakout_1_2()
poke  = Poke(board.port_3, rising_event='poke', falling_event='poke_out') 

# State machine.

states = ['wait_for_poke','poked']

events = ['poke', 'poke_out']

initial_state = 'wait_for_poke'

v.state_dur = 500

def wait_for_poke(event):
    if event == 'poke':
        goto_state('poked')

def poked(event):
    if event=='entry':
        poke.LED.on()
        poke.SOL.on()
    elif event=='exit':
        poke.LED.off()
        poke.SOL.off()
    elif event == 'poke_out':
        goto_state('wait_for_poke')
