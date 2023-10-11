from pycontrol_mcu.hardware import Digital_output


class LED_driver(Digital_output):
    def __init__(self, port):
        super().__init__(port.DIO_A)
