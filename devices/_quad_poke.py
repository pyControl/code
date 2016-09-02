from pyControl.hardware import *

class _Poke():
    def __init__(self, input_pin, LED_pin,rising_event, falling_event, debounce):
        self.input = Digital_input(input_pin, rising_event, falling_event, debounce)
        if LED_pin: self.LED = Digital_output(LED_pin)

    def value(self):
        return self.input.value()

class Quad_poke():
    # 4 IR beams, 3 of which have LEDs, 1 solenoid,
    def __init__(self, ports, rising_event_A = None, falling_event_A = None,
                              rising_event_B = None, falling_event_B = None, 
                              rising_event_C = None, falling_event_C = None, 
                              rising_event_D = None, falling_event_D = None, debounce = 5):
        port_1, port_2 = ports # ports argument must be list of two Ports objects.
        self.poke_A = _Poke(port_1.DIO_A, port_1.POW_A, rising_event_A, falling_event_A, debounce)
        self.poke_B = _Poke(port_1.DIO_B, port_1.POW_B, rising_event_B, falling_event_B, debounce)
        self.poke_C = _Poke(port_2.DIO_A, port_2.POW_A, rising_event_C, falling_event_C, debounce)
        self.poke_D = _Poke(port_2.DIO_B, None        , rising_event_D, falling_event_D, debounce)
        self.SOL = Digital_output(port_2.POW_B)