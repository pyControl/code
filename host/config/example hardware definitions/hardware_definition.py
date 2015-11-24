from pyControl.hardware import *

board = devboard_1_0
pull  = pyb.Pin.PULL_DOWN

# Instantiate Devices.

left_poke   = Poke(rising_event = 'left_poke', falling_event = 'left_poke_out')
right_poke  = Poke(rising_event = 'right_poke', falling_event = 'left_poke_out')
center_poke = Double_poke(rising_event_A = 'high_poke',  falling_event_A = 'high_poke_out',
                          rising_event_B = 'low_poke' ,  falling_event_B = 'low_poke_out')

houselight = center_poke.SOL

# Connect devices to control board.

connect_device(left_poke  , board['ports'][1], pull)
connect_device(center_poke, board['ports'][2], pull)
connect_device(right_poke , board['ports'][3], pull)


