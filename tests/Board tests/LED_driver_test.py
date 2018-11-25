# Connect breakout board 1.2 to the computer, plug in the 12V power supply.  
# Connect an LED_driver board to port 3 on the breakout board and plug an LED 
# headstage into the LED driver. The LED will flash on and off, use the range
# selector switch and power knob on the LED driver to vary the LED power. 
# LED will be very bright at high powers so be careful not to look directly at it. 

from pyControl.utility import *
from devices import Breakout_1_2, LED_driver

board = Breakout_1_2()
LED = LED_driver(board.port_3)

# States and events.

states = ['LED_on',
          'LED_off']

events = []

initial_state = 'LED_off'
  
# Define behaviour. 

def LED_on(event):
    if event == 'entry':
        timed_goto_state('LED_off', 0.5 * second)
        LED.on()
    elif event == 'exit':
        LED.off()

def LED_off(event):
    if event == 'entry':
        timed_goto_state('LED_on', 0.5 * second)

def run_end():  # Turn off hardware at end of run.
    LED.off()



