# Identical to the button example but using named imports rather
# than the 'from module import *' syntax.  This way is more 
# 'Pythonic' but results somewhat more verbose task code.  You can 
# use whichever import style you prefer in your task code.

import pyControl.utility as pc 
import devices as dv
  
# Define hardware 
  
button = dv.Digital_input('X17', rising_event='button_press', pull='up') # pyboard usr button.
LED    = dv.Digital_output('B4') 
  
# States and events. 
  
states = ['LED_on', 
          'LED_off'] 
  
events = ['button_press'] 
  
initial_state = 'LED_off' 
  
# Variables 
  
pc.v.press_n = 0 
  
# State behaviour functions. 
  
def LED_off(event): 
    if event == 'button_press': 
        pc.v.press_n = pc.v.press_n + 1
        pc.print('Press number {}'.format(pc.v.press_n))
        if pc.v.press_n == 3: 
            pc.goto_state('LED_on') 
  
def LED_on(event): 
    if event == 'entry': 
        LED.on() 
        pc.timed_goto_state('LED_off', 1*pc.second) 
        pc.v.press_n = 0 
    elif event == 'exit': 
        LED.off() 