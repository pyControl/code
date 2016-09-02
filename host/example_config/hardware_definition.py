from devices import *

board = Devboard_1_0()

# Instantiate Devices.
left_poke   = Poke(board.port_1, rising_event = 'left_poke' , falling_event = 'left_poke_out' )
right_poke  = Poke(board.port_3, rising_event = 'right_poke', falling_event = 'right_poke_out')
center_poke = Double_poke(board.port_2, rising_event_A  = 'high_poke', falling_event_A = 'high_poke_out',
                                        rising_event_B  = 'low_poke' , falling_event_B = 'low_poke_out')

# Aliases
houselight = center_poke.SOL