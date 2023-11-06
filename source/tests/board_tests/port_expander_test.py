# Install the driver files for the Port Expander (see
# https://pycontrol.readthedocs.io/en/latest/user-guide/hardware/#more-devices).
# Connect port expander board to port 3 of the breakout board 1.2, connect
# breakout board to the computer, plug in the 12V power supply. Connect a
#  breakout tester 1.0 board to each RJ45 port on the port expander in turn.
# LEDs +12V and +5V on the tester should be on continuously and LEDs
# DIO-A, DIO-B, POW-A, POW-B should cycle on and off.

from pyControl.utility import *
from devices import Breakout_1_2, Digital_output, Port_expander

# Hardware

board = Breakout_1_2()
port_exp = Port_expander(board.port_3)
DIO_1A = Digital_output(port_exp.port_1.DIO_A, inverted=True)
DIO_1B = Digital_output(port_exp.port_1.DIO_B, inverted=True)
DIO_2A = Digital_output(port_exp.port_2.DIO_A, inverted=True)
DIO_2B = Digital_output(port_exp.port_2.DIO_B, inverted=True)
DIO_3A = Digital_output(port_exp.port_3.DIO_A, inverted=True)
DIO_3B = Digital_output(port_exp.port_3.DIO_B, inverted=True)
DIO_4A = Digital_output(port_exp.port_4.DIO_A, inverted=True)
DIO_4B = Digital_output(port_exp.port_4.DIO_B, inverted=True)
DIO_5A = Digital_output(port_exp.port_5.DIO_A, inverted=True)
DIO_5B = Digital_output(port_exp.port_5.DIO_B, inverted=True)
DIO_6A = Digital_output(port_exp.port_6.DIO_A, inverted=True)
DIO_6B = Digital_output(port_exp.port_6.DIO_B, inverted=True)
DIO_7A = Digital_output(port_exp.port_7.DIO_A, inverted=True)
DIO_7B = Digital_output(port_exp.port_7.DIO_B, inverted=True)
DIO_8A = Digital_output(port_exp.port_8.DIO_A, inverted=True)
DIO_8B = Digital_output(port_exp.port_8.DIO_B, inverted=True)
POW_1A = Digital_output(port_exp.port_1.POW_A)
POW_1B = Digital_output(port_exp.port_1.POW_B)
POW_2A = Digital_output(port_exp.port_2.POW_A)
POW_2B = Digital_output(port_exp.port_2.POW_B)
POW_3A = Digital_output(port_exp.port_3.POW_A)
POW_3B = Digital_output(port_exp.port_3.POW_B)
POW_4A = Digital_output(port_exp.port_4.POW_A)
POW_4B = Digital_output(port_exp.port_4.POW_B)
POW_5A = Digital_output(port_exp.port_5.POW_A)
POW_5B = Digital_output(port_exp.port_5.POW_B)
POW_6A = Digital_output(port_exp.port_6.POW_A)
POW_6B = Digital_output(port_exp.port_6.POW_B)
POW_5A = Digital_output(port_exp.port_5.POW_A)
POW_5B = Digital_output(port_exp.port_5.POW_B)
POW_6A = Digital_output(port_exp.port_6.POW_A)
POW_6B = Digital_output(port_exp.port_6.POW_B)
POW_7A = Digital_output(port_exp.port_7.POW_A)
POW_7B = Digital_output(port_exp.port_7.POW_B)
POW_8A = Digital_output(port_exp.port_8.POW_A)
POW_8B = Digital_output(port_exp.port_8.POW_B)

# States and events.

states = ["DIO_A", "DIO_B", "POW_A", "POW_B"]

events = []

initial_state = "DIO_A"

# Define behaviour.


def DIO_A(event):
    if event == "entry":
        timed_goto_state("DIO_B", 200 * ms)
        for x in (DIO_1A, DIO_2A, DIO_3A, DIO_4A, DIO_5A, DIO_6A, DIO_7A, DIO_8A):
            x.on()
    elif event == "exit":
        for x in (DIO_1A, DIO_2A, DIO_3A, DIO_4A, DIO_5A, DIO_6A, DIO_7A, DIO_8A):
            x.off()


def DIO_B(event):
    if event == "entry":
        timed_goto_state("POW_A", 200 * ms)
        for x in (DIO_1B, DIO_2B, DIO_3B, DIO_4B, DIO_5B, DIO_6B, DIO_7B, DIO_8B):
            x.on()
    elif event == "exit":
        for x in (DIO_1B, DIO_2B, DIO_3B, DIO_4B, DIO_5B, DIO_6B, DIO_7B, DIO_8B):
            x.off()


def POW_A(event):
    if event == "entry":
        timed_goto_state("POW_B", 200 * ms)
        for x in (POW_1A, POW_2A, POW_3A, POW_4A, POW_5A, POW_6A, POW_7A, POW_8A):
            x.on()
    elif event == "exit":
        for x in (POW_1A, POW_2A, POW_3A, POW_4A, POW_5A, POW_6A, POW_7A, POW_8A):
            x.off()


def POW_B(event):
    if event == "entry":
        timed_goto_state("DIO_A", 200 * ms)
        for x in (POW_1B, POW_2B, POW_3B, POW_4B, POW_5B, POW_6B, POW_7B, POW_8B):
            x.on()
    elif event == "exit":
        for x in (POW_1B, POW_2B, POW_3B, POW_4B, POW_5B, POW_6B, POW_7B, POW_8B):
            x.off()
