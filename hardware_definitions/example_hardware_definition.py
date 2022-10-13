# This hardware definition specifies that 3 pokes are plugged into ports 1-3 and a speaker into
# port 4 of breakout board version 1.2.  The houselight is plugged into the center pokes solenoid socket.

from devices import *

board = Breakout_1_2()

# Instantiate Devices.
left_poke   = Poke(board.port_1, rising_event = 'left_poke'  , falling_event = 'left_poke_out' )
center_poke = Poke(board.port_2, rising_event = 'center_poke', falling_event = 'center_poke_out')
right_poke  = Poke(board.port_3, rising_event = 'right_poke' , falling_event = 'right_poke_out')

speaker = Audio_board(board.port_4)

# Aliases
houselight = center_poke.SOL 