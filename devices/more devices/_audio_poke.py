import pyControl.hardware as _h
import pyControl.audio as _a

class Audio_poke():
    # Single IR beam, LED and Solenoid.  Audio amplifier to drive speaker.
    def __init__(self, port, rising_event = None, falling_event = None, debounce = 5):
        assert port.DAC is not None, '! Audio poke needs port with DAC.'
        self.input = _h.Digital_input(port.DIO_A, rising_event, falling_event, debounce)
        self.LED = _h.Digital_output(port.POW_A)
        self.SOL = _h.Digital_output(port.POW_B)
        if port.POW_C is not None:
            self.POW_C = _h.Digital_output(port.POW_C)
        self.audio_output = _a.Audio_output(port.DAC)

    def value(self):
        return self.input.value()