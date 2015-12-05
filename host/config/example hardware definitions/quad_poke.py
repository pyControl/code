from pyControl.hardware import *

board = devboard_1_0

# Instantiate devices.

quad_poke = Quad_poke(rising_event_A = 'high_poke',
	                  rising_event_B = 'left_poke',
	                  rising_event_C = 'right_poke',
	                  rising_event_D = 'center_poke')

# Connect devices.

connect_device(quad_poke, [board['ports'][1],board['ports'][2]])

# Aliases.

high_poke   = quad_poke.poke_A
left_poke   = quad_poke.poke_B
right_poke  = quad_poke.poke_C
center_poke = quad_poke.poke_D

house_light = quad_poke.SOL



