from pyControl.hardware import Digital_output, Digital_input


class Poke:
    # Single IR beam, LED and Solenoid.
    def __init__(self, port, rising_event=None, falling_event=None, debounce=5):
        self.input = Digital_input(port.DIO_A, rising_event, falling_event, debounce)
        self.LED = Digital_output(port.POW_A)
        self.SOL = Digital_output(port.POW_B)
        if port.POW_C is not None:
            self.POW_C = Digital_output(port.POW_C)

    def value(self):
        return self.input.value()


class _Poke:
    # Poke class used in multi-poke devices.
    def __init__(self, input_pin, LED_pin, rising_event, falling_event, debounce):
        self.input = Digital_input(input_pin, rising_event, falling_event, debounce)
        if LED_pin:
            self.LED = Digital_output(LED_pin)

    def value(self):
        return self.input.value()
