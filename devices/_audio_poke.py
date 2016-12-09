from pyControl.hardware import *
from pyControl.audio import Audio_output

class Audio_poke():
    # Single IR beam, LED and Solenoid.  Audio amplifier to drive speaker.
    def __init__(self, port, rising_event = None, falling_event = None, debounce = 5):
        assert port.DAC is not None, '! Audio poke needs port with DAC.'
        self.input = Digital_input(port.DIO_A, rising_event, falling_event, debounce)
        self.LED = Digital_output(port.POW_A)
        self.SOL = Digital_output(port.POW_B)
        if port.POW_C is not None:
            self.POW_C = Digital_output(port.POW_C)
        self.audio_output = Audio_output(port.DAC)

    def value(self):
        return self.input.value()