# Connect breakout board 1.2 to the computer, plug in the 12V power supply.  
# Connect a Stepper motor driver board to port 3 on the breakout board and 
# connect a stepper motor to it. The stepper motor will rotate forward and 
# backward.

from pyControl.utility import *
from devices import Breakout_1_2, Stepper_motor

board = Breakout_1_2()
motor = Stepper_motor(board.port_3) 

# States and events.

states = ['forward',
          'backward']

events = []

initial_state = 'forward'
  
# Define behaviour. 

def forward(event):
    if event == 'entry':
        timed_goto_state('backward', 0.5 * second)
        motor.forward(step_rate=100, n_steps=25)

def backward(event):
    if event == 'entry':
        timed_goto_state('forward', 0.5 * second)
        motor.backward(step_rate=100, n_steps=25)

def run_end():  # Turn off hardware at end of run.
    motor.stop()



