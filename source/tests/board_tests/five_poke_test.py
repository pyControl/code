# Connect breakout board 1.2 to the computer, plug in the 12V power supply.
# Connect port 1 on the Five poke board to port 1 on the breakout board.
# Connect port 2 on the Five poke board to port 3 on the breakout board.
# Run this task file using the pyControl GUI.
# Poke in each port of the 5 poke in turn, the light on the poke will
# illuminate for 500ms when you poke it.

from pyControl.utility import *
from devices import Breakout_1_2, Five_poke

# Define hardware

board = Breakout_1_2()
five_poke = Five_poke(ports=[board.port_1, board.port_3])

# State machine.

states = [
    "wait_for_poke",
    "state_1",
    "state_2",
    "state_3",
    "state_4",
    "state_5",
]

events = [
    "poke_1",
    "poke_2",
    "poke_3",
    "poke_4",
    "poke_5",
]

initial_state = "wait_for_poke"

v.state_dur = 500


def wait_for_poke(event):
    if event == "poke_1":
        goto_state("state_1")
    elif event == "poke_2":
        goto_state("state_2")
    elif event == "poke_3":
        goto_state("state_3")
    elif event == "poke_4":
        goto_state("state_4")
    elif event == "poke_5":
        goto_state("state_5")


def state_1(event):
    if event == "entry":
        five_poke.poke_1.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        five_poke.poke_1.LED.off()


def state_2(event):
    if event == "entry":
        five_poke.poke_2.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        five_poke.poke_2.LED.off()


def state_3(event):
    if event == "entry":
        five_poke.poke_3.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        five_poke.poke_3.LED.off()


def state_4(event):
    if event == "entry":
        five_poke.poke_4.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        five_poke.poke_4.LED.off()


def state_5(event):
    if event == "entry":
        five_poke.poke_5.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        five_poke.poke_5.LED.off()
