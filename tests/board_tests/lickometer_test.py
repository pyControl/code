# Install the driver file for the Lickometer (see
# https://pycontrol.readthedocs.io/en/latest/user-guide/hardware/#more-devices).
# Connect breakout board 1.2 to the computer, plug in the 12V power supply.
# Connect a Lickometer to port 1 of the breakout board. Plug a houselight into
# the SOL-1 and SOL-2 ports on the Lickometer. When you make an electrical
# connection between LK1 and GND the houselight connected to SOL-1 will turn on.
# When you make an electrical connection between LK2 and GND the houselight
# connected to SOL-2 will turn on.

from pyControl.utility import *
from devices import Breakout_1_2, Lickometer

# Define hardware

board = Breakout_1_2()
lickometer = Lickometer(
    board.port_1,
    rising_event_A="lick_1",
    falling_event_A="lick_1_off",
    rising_event_B="lick_2",
    falling_event_B="lick_2_off",
)

# State machine.

states = ["state1"]

events = ["lick_1", "lick_1_off", "lick_2", "lick_2_off"]

initial_state = "state1"


def state1(event):
    if event == "lick_1":
        lickometer.SOL_1.on()
    elif event == "lick_1_off":
        lickometer.SOL_1.off()
    elif event == "lick_2":
        lickometer.SOL_2.on()
    elif event == "lick_2_off":
        lickometer.SOL_2.off()
