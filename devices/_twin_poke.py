from pyControl.hardware import *

class _Poke():
    def __init__(self, input_pin, LED_pin, rising_event, falling_event, debounce):
        self.input = Digital_input(input_pin, rising_event, falling_event, debounce)
        if LED_pin: self.LED = Digital_output(LED_pin)

    def value(self):
        return self.input.value()

class Twin_poke():
    # Two IR beams, each with their own LED.
    def __init__(self, port, rising_event_A = None, falling_event_A = None,
                 rising_event_B = None, falling_event_B = None, debounce = 5):
        self.poke_A = _Poke(port_1.DIO_A, port_1.POW_A, rising_event_A, falling_event_A, debounce)
        self.poke_B = _Poke(port_1.DIO_B, port_1.POW_B, rising_event_A, falling_event_A, debounce)
        self.LED = Digital_output_group([self.poke_A.LED, self.poke_B.LED])