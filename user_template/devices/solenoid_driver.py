from pyControl.hardware import Digital_output


class Solenoid_driver:
    # 5 solenoid connectors controled from one port.
    def __init__(self, port):
        assert port.POW_C is not None, "! Solenoid driver needs port with POW_C"
        self.SOL_1 = Digital_output(port.POW_A)
        self.SOL_2 = Digital_output(port.POW_B)
        self.SOL_3 = Digital_output(port.POW_C)
        self.SOL_4 = Digital_output(port.DIO_A)
        self.SOL_5 = Digital_output(port.DIO_B)
