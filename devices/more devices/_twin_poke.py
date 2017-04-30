import pyControl.hardware as _h
from devices._poke import _Poke

class Twin_poke():
    # Two IR beams, each with their own LED.
    def __init__(self, port, rising_event_A = None, falling_event_A = None,
                 rising_event_B = None, falling_event_B = None, debounce = 5):
        self.poke_A = _Poke(port.DIO_A, port.POW_A, rising_event_A, falling_event_A, debounce)
        self.poke_B = _Poke(port.DIO_B, port.POW_B, rising_event_B, falling_event_B, debounce)
        self.LED = _h.Digital_output_group([self.poke_A.LED, self.poke_B.LED])