# Connect breakout board 1.2 to the computer, plug in the 12V power supply.  
# Connect a breakout tester 1.0 board to each RJ45 port in turn. In every port
# LEDs +12V and +5V on the tester should be on continuously and LEDs
# DIO-A, DIO-B, POW-A, POW-B should cycle on and off. In ports 1-4 the LED DP/C
# should also cycle on and off. Connect a tester board to each BNC socket on 
# the breakout in turn, the BNC LED should turn on and off.

from pyControl.utility import *
from devices import Breakout_1_2, Digital_output

# Hardware

board = Breakout_1_2()
DIO_1A = Digital_output(board.port_1.DIO_A, inverted=True)
DIO_1B = Digital_output(board.port_1.DIO_B, inverted=True)
DIO_2A = Digital_output(board.port_2.DIO_A, inverted=True)
DIO_2B = Digital_output(board.port_2.DIO_B, inverted=True)
DIO_3A = Digital_output(board.port_3.DIO_A, inverted=True)
DIO_3B = Digital_output(board.port_3.DIO_B, inverted=True)
DIO_3C = Digital_output(board.port_3.DIO_C, inverted=True)
DIO_4A = Digital_output(board.port_4.DIO_A, inverted=True)
DIO_4B = Digital_output(board.port_4.DIO_B, inverted=True)
DIO_4C = Digital_output(board.port_4.DIO_C, inverted=True)
DIO_5A = Digital_output(board.port_5.DIO_A, inverted=True)
DIO_5B = Digital_output(board.port_5.DIO_B, inverted=True)
DIO_6A = Digital_output(board.port_6.DIO_A, inverted=True)
DIO_6B = Digital_output(board.port_6.DIO_B, inverted=True)
POW_1A = Digital_output(board.port_1.POW_A)
POW_1B = Digital_output(board.port_1.POW_B)
POW_1C = Digital_output(board.port_1.POW_C)
POW_2A = Digital_output(board.port_2.POW_A)
POW_2B = Digital_output(board.port_2.POW_B)
POW_2C = Digital_output(board.port_2.POW_C)
POW_3A = Digital_output(board.port_3.POW_A)
POW_3B = Digital_output(board.port_3.POW_B)
POW_4A = Digital_output(board.port_4.POW_A)
POW_4B = Digital_output(board.port_4.POW_B)
POW_5A = Digital_output(board.port_5.POW_A)
POW_5B = Digital_output(board.port_5.POW_B)
POW_6A = Digital_output(board.port_6.POW_A)
POW_6B = Digital_output(board.port_6.POW_B)
BNC_2 = Digital_output(board.BNC_2) # The other BNC pins double as port pins.

# States and events.

states = ['DIO_A',
          'DIO_B',
          'POW_A',
          'POW_B',
          'DP_C']

events = []

initial_state = 'DIO_A'
        
# Define behaviour. 

def DIO_A(event):
    if event == 'entry':
        timed_goto_state('DIO_B', 200*ms)
        for x in (DIO_1A, DIO_2A, DIO_3A, DIO_4A, DIO_5A, DIO_6A):
            x.on()
    elif event == 'exit':
        for x in (DIO_1A, DIO_2A, DIO_3A, DIO_4A, DIO_5A, DIO_6A):
            x.off()

def DIO_B(event):
    if event == 'entry':
        timed_goto_state('POW_A', 200*ms)
        for x in (DIO_1B, DIO_2B, DIO_3B, DIO_4B, DIO_5B, DIO_6B):
            x.on()
    elif event == 'exit':
        for x in (DIO_1B, DIO_2B, DIO_3B, DIO_4B, DIO_5B, DIO_6B):
            x.off()

def POW_A(event):
    if event == 'entry':
        timed_goto_state('POW_B', 200*ms)
        for x in (POW_1A, POW_2A, POW_3A, POW_4A, POW_5A, POW_6A):
            x.on()
    elif event == 'exit':
        for x in (POW_1A, POW_2A, POW_3A, POW_4A, POW_5A, POW_6A):
            x.off()

def POW_B(event):
    if event == 'entry':
        timed_goto_state('DP_C', 200*ms)
        for x in (POW_1B, POW_2B, POW_3B, POW_4B, POW_5B, POW_6B):
            x.on()
    elif event == 'exit':
        for x in (POW_1B, POW_2B, POW_3B, POW_4B, POW_5B, POW_6B):
            x.off()

def DP_C(event):
    if event == 'entry':
        timed_goto_state('DIO_A', 200*ms)
        for x in (POW_1C, POW_2C, DIO_3C, DIO_4C, BNC_2):
            x.on()
    elif event == 'exit':
        for x in (POW_1C, POW_2C, DIO_3C, DIO_4C, BNC_2):
            x.off()