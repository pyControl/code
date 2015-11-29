from pyControl.hardware import *

board = devboard_1_0
pull  = pyb.Pin.PULL_DOWN

# Instantiate Devices.

left_poke  = Poke(rising_event = 'left_poke' , falling_event = 'left_poke_out' )
right_poke = Poke(rising_event = 'right_poke', falling_event = 'right_poke_out')
high_poke  = Poke(rising_event = 'high_poke' , falling_event = 'high_poke_out' )
low_poke   = Poke(rising_event = 'low_poke'  , falling_event = 'low_poke_out'  )

high_poke.SOL = left_poke.SOL  # Side poke solenoids are controlling high and low poke
low_poke.SOL  = right_poke.SOL # reward delivery.

houselight      = Digital_output()
houselight_red  = Digital_output()
opto_stim       = Digital_output()

# Connect devices to control board.

left_poke.connect( board['ports'][1], pull)
right_poke.connect(board['ports'][3], pull)

high_poke.connect(input_pin = board['ports'][2]['DIO_A'], 
                  LED_pin   = board['ports'][2]['POW_B'], pull = pull)
low_poke.connect( input_pin = board['ports'][2]['DIO_B'], 
                  LED_pin   = board['ports'][2]['POW_A'], pull = pull)

connect_device(houselight    , 'Y5')
connect_device(houselight_red, 'Y1')
connect_device(opto_stim     , 'X12')


