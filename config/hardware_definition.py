# This hardware definition specifies that 3 pokes are plugged into ports 1-3 and a speaker into
# port 4 of breakout board version 1.2.  The houselight is plugged into the center pokes solenoid socket.

from devices import *
import pyb
from pyControl.hardware import *

board = Breakout_1_2()

# Instantiate digital output connected to BNC_1.
Lickometer = Lickometer(port=board.port_1)
solenoid = Lickometer.SOL_1
sync_output = Rsync(pin=board.BNC_1, mean_IPI=1000, pulse_dur=10) # Instantiate Rsync object on breakout board BNC_1

