import pyControl.hardware as _h

class Devboard_1_0(_h.Mainboard):
    def __init__(self):
        # Inputs and outputs.
        self.port_1 = _h.Port(DIO_A='Y1', DIO_B='Y4', POW_A='Y7' , POW_B='Y8')
        self.port_2 = _h.Port(DIO_A='Y2', DIO_B='Y5', POW_A='Y9' , POW_B='Y10')
        self.port_3 = _h.Port(DIO_A='Y3', DIO_B='Y6', POW_A='Y11', POW_B='Y12')
        self.BNC_1 = 'X7'
        self.BNC_2 = 'X8'
        self.DAC_1 = 'X5'
        self.DAC_2 = 'X6'
        # Set default pullup/pulldown resistors.
        self.set_pull_updown({'down': ['Y1','Y4','Y2','Y5','Y3','Y6']})