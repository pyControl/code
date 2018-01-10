import pyControl.hardware as _h

class LED_driver(_h.Digital_output):
    def __init__(self,  port):
        super().__init__(port.DIO_A, pulse_enabled=True)