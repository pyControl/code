# Connect breakout board 1.2 to the computer, plug in the 12V power supply.
# Connect an audio board to port 3 on the breakout board and plug a speaker into
# the audio board.  The speaker should play white noise at different volumes.

from pyControl.utility import *
from devices import Breakout_1_2, Audio_board

board = Breakout_1_2()
speaker = Audio_board(board.port_3)

# States and events.

states = ["noise_on", "noise_off"]

events = []

initial_state = "noise_off"

# Variables

v.volume = 0

# Define behaviour.


def noise_on(event):
    if event == "entry":
        timed_goto_state("noise_off", 0.5 * second)
        speaker.noise()
    elif event == "exit":
        speaker.off()


def noise_off(event):
    if event == "entry":
        v.volume = (v.volume + 10) % 100
        speaker.set_volume(v.volume + 10)
        timed_goto_state("noise_on", 0.5 * second)


def run_end():  # Turn off hardware at end of run.
    speaker.off()
