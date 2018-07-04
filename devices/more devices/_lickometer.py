import pyControl.hardware as _h

class Lickometer():
    # Two lick detectors and two solenoids.
    def __init__(self,  port, rising_event_A='lick_1', falling_event_A='lick_1_off',
                rising_event_B='lick_2', falling_event_B='lick_2_off', debounce=5):
        self.lick_1 = _h.Digital_input(port.DIO_A, rising_event_A, falling_event_A, debounce)
        self.lick_2 = _h.Digital_input(port.DIO_B, rising_event_B, falling_event_B, debounce)
        self.SOL_1  = _h.Digital_output(port.POW_A)
        self.SOL_2  = _h.Digital_output(port.POW_B)