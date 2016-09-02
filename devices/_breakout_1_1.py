import pyb
from pyControl import hardware

class Breakout_1_1():
    def __init__(self):
        # Inputs and outputs.
        self.port_1 = hardware.Port(DIO_A='Y1', DIO_B='X1' , POW_A='Y7' , POW_B='Y8' , C='Y11')
        self.port_2 = hardware.Port(DIO_A='Y2', DIO_B='X2' , POW_A='X4' , POW_B='X18', C='Y12')
        self.port_3 = hardware.Port(DIO_A='Y3', DIO_B='X3' , POW_A='X7' , POW_B='X19')
        self.port_4 = hardware.Port(DIO_A='Y4', DIO_B='X11', POW_A='X8' , POW_B='X20')
        self.port_5 = hardware.Port(DIO_A='Y5', DIO_B='Y6' , POW_A='X21', POW_B='X22')
        self.port_6 = hardware.Port(DIO_A='Y9', DIO_B='Y10', POW_A='X9' , POW_B='X10')        
        self.BNC_1  = 'X12'
        self.BNC_2  = 'Y10'
        self.DAC_1  = 'X5'
        self.DAC_2  = 'X6'
        self.button = 'X17'
