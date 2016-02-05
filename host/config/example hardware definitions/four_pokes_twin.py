from pyControl.devices import *

board = breakout_1_0
pull  = pyb.Pin.PULL_NONE

# Instantiate Devices.

left_poke   = Poke(rising_event = 'left_poke' , falling_event = 'left_poke_out' )
right_poke  = Poke(rising_event = 'right_poke', falling_event = 'right_poke_out')
center_poke = Twin_poke(rising_event_A  = 'high_poke', falling_event_A = 'high_poke_out',
                        rising_event_B  = 'low_poke' , falling_event_B = 'low_poke_out')

houselight      = Digital_output()
houselight_red  = Digital_output()
opto_stim       = Digital_output()

# Connect devices to control board.

connect_device(left_poke  , board['ports'][1], pull)
connect_device(center_poke, board['ports'][2], pull)
connect_device(right_poke , board['ports'][3], pull)

connect_device(houselight    , 'Y5')
connect_device(houselight_red, 'Y1')
connect_device(opto_stim     , 'X12')

#Aliases

high_poke = center_poke.poke_A
low_poke  = center_poke.poke_B 

high_poke.SOL = left_poke.SOL  # Side poke solenoids are controlling high and low poke
low_poke.SOL  = right_poke.SOL # reward delivery.
