# Install the driver file for the Five_poke (see
# https://pycontrol.readthedocs.io/en/latest/user-guide/hardware/#more-devices).
# Connect breakout board 1.2 to the computer, plug in the 12V power supply.
# Connect port 1 on the Five poke board to port 1 on the breakout board.
# Connect port 2 on the Five poke board to port 3 on the breakout board.
# Poke in each port of the 5 poke in turn, the light on the poke will illuminate
# after you poke it.

from pyControl.utility import *
from devices import Breakout_1_2, Five_poke

# Define hardware

board = Breakout_1_2()
five_poke = Five_poke(ports=[board.port_1, board.port_3])

# State machine.

states = ["wait_for_poke", "state1", "state2", "state3", "state4", "state5"]

events = [
    "poke_1",
    "poke_1_out",
    "poke_2",
    "poke_2_out",
    "poke_3",
    "poke_3_out",
    "poke_4",
    "poke_4_out",
    "poke_5",
    "poke_5_out",
]

initial_state = "wait_for_poke"

v.state_dur = 500


def wait_for_poke(event):
    if event == "poke_1_out":
        goto_state("state1")
    elif event == "poke_2_out":
        goto_state("state2")
    elif event == "poke_3_out":
        goto_state("state3")
    elif event == "poke_4_out":
        goto_state("state4")
    elif event == "poke_5_out":
        goto_state("state5")


def state1(event):
    if event == "entry":
        five_poke.poke_1.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        five_poke.poke_1.LED.off()


def state2(event):
    if event == "entry":
        five_poke.poke_2.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        five_poke.poke_2.LED.off()


def state3(event):
    if event == "entry":
        five_poke.poke_3.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        five_poke.poke_3.LED.off()


def state4(event):
    if event == "entry":
        five_poke.poke_4.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        five_poke.poke_4.LED.off()


def state5(event):
    if event == "entry":
        five_poke.poke_5.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        five_poke.poke_5.LED.off()
