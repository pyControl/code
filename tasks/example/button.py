# A simple state machine which turns the blue LED on the pyboard on for 1 
# second when the usr pushbutton on the pyboard is pressed three times.  
# Does not require any hardware except a micropython board.

from pyControl.utility import * 
from devices import * 
  
# Define hardware 
  
button = Digital_input('X17', rising_event='button_press', pull='up') # pyboard usr button.
LED    = Digital_output('B4') 
  
# States and events. 
  
states = ['LED_on', 
          'LED_off'] 
  
events = ['button_press'] 
  
initial_state = 'LED_off' 
  
# Variables 
  
v.press_n = 0 
  
# State behaviour functions. 
  
def LED_off(event): 
    if event == 'button_press': 
        v.press_n = v.press_n + 1
        print('Press number {}'.format(v.press_n))
        if v.press_n == 3: 
            goto_state('LED_on') 
  
def LED_on(event): 
    if event == 'entry': 
        LED.on() 
        timed_goto_state('LED_off', 1*second) 
        v.press_n = 0 
    elif event == 'exit': 
        LED.off() 