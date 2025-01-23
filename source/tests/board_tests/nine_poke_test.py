# Connect breakout board 1.2 to the computer, plug in the 12V power supply.
# Connect a Nine_Poke board to port 3 on the breakout board.
# Run this task file using the pyControl GUI.
# Poke in each port of the 9 poke in turn, the light on the poke will illuminate
# for 500ms when you poke it.

from pyControl.utility import *
from devices import Breakout_1_2, nine_poke

# Define hardware

board = Breakout_1_2()
nine_poke = Nine_poke(port=board.port_3)

# State machine.

states = [
    "wait_for_poke",
    "state_1",
    "state_2",
    "state_3",
    "state_4",
    "state_5",
    "state_6",
    "state_7",
    "state_8",
    "state_9",
]

events = [
    "poke_1",
    "poke_2",
    "poke_3",
    "poke_4",
    "poke_5",
    "poke_6",
    "poke_7",
    "poke_8",
    "poke_9",
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
    elif event == "poke_6":
        goto_state("state_6")
    elif event == "poke_7":
        goto_state("state_7")
    elif event == "poke_8":
        goto_state("state_8")
    elif event == "poke_9":
        goto_state("state_9")


def state_1(event):
    if event == "entry":
        nine_poke.poke_1.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        nine_poke.poke_1.LED.off()


def state_2(event):
    if event == "entry":
        nine_poke.poke_2.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        nine_poke.poke_2.LED.off()


def state_3(event):
    if event == "entry":
        nine_poke.poke_3.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        nine_poke.poke_3.LED.off()


def state_4(event):
    if event == "entry":
        nine_poke.poke_4.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        nine_poke.poke_4.LED.off()


def state_5(event):
    if event == "entry":
        nine_poke.poke_5.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        nine_poke.poke_5.LED.off()


def state_6(event):
    if event == "entry":
        nine_poke.poke_6.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        nine_poke.poke_6.LED.off()


def state_7(event):
    if event == "entry":
        nine_poke.poke_7.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        nine_poke.poke_7.LED.off()


def state_8(event):
    if event == "entry":
        nine_poke.poke_8.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        nine_poke.poke_8.LED.off()


def state_9(event):
    if event == "entry":
        nine_poke.poke_9.LED.on()
        timed_goto_state("wait_for_poke", v.state_dur)
    elif event == "exit":
        nine_poke.poke_9.LED.off()
