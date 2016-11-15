from pyControl.hardware import *

class Double_poke():
    # Two IR beams, single LED and Solenoid.
    def __init__(self,  port, rising_event_A = None, falling_event_A = None,
                rising_event_B = None, falling_event_B = None, debounce = 5):
        self.input_A = Digital_input(port.DIO_A, rising_event_A, falling_event_A, debounce)
        self.input_B = Digital_input(port.DIO_B, rising_event_B, falling_event_B, debounce)
        self.LED     = Digital_output(port.POW_A)
        self.SOL     = Digital_output(port.POW_B)
        if port.POW_C is not None:
            self.POW_C = Digital_output(port.POW_C)