# Connect breakout board 1.2 to the computer, plug in the 12V power supply.
# Connect an audio player to port 1 on the breakout board and plug a speaker into
# each of the two speaker sockets.  Get a micro SD card, format it in FAT32, create
# a folder on the SD card called '01' and put a short wav file with name '001.wav'
# in the folder.  You can use a wav file from the sample pack that can be
# downloaded from this address address: http://smd-records.com/tr808/?page_id=14
# Put the folder in the SD card socket on the audio player. Run the task and the
# wav file should play alternately from each speaker at two different volumes.

from pyControl.utility import *
from devices import Breakout_1_2, Audio_player

board = Breakout_1_2()
player = Audio_player(board.port_1)

# States and events.

states = ["play_sound", "wait"]

events = []

initial_state = "wait"

# Variables

v.i = 0
v.volumes = [30, 30, 15, 15]
v.speaker_enabled = True

# Define behaviour.


def wait(event):
    if event == "entry":
        timed_goto_state("play_sound", 0.5 * second)
        v.speaker_enabled = not v.speaker_enabled
        player.set_volume(v.volumes[v.i])
        v.i = (v.i + 1) % 4
        player.set_enabled(left=v.speaker_enabled, right=not v.speaker_enabled)


def play_sound(event):
    if event == "entry":
        timed_goto_state("wait", 0.5 * second)
        player.play(folder_num=1, file_num=1)
