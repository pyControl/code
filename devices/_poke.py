from pyControl.hardware import *

class Poke():
    # Single IR beam, LED and Solenoid.
    def __init__(self, port, rising_event = None, falling_event = None, debounce = 5):
        self.input = Digital_input(port.DIO_A, rising_event, falling_event, debounce)
        self.LED = Digital_output(port.POW_A)
        self.SOL = Digital_output(port.POW_B)

    def value(self):
        return self.input.value()