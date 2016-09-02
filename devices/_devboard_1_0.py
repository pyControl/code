import pyb
from pyControl import hardware

class Devboard_1_0():
    def __init__(self):
        # Inputs and outputs.
        self.port_1 = hardware.Port(DIO_A='Y1', DIO_B='Y4', POW_A='Y7' , POW_B='Y8')
        self.port_2 = hardware.Port(DIO_A='Y2', DIO_B='Y5', POW_A='Y9' , POW_B='Y10')
        self.port_3 = hardware.Port(DIO_A='Y3', DIO_B='Y6', POW_A='Y11', POW_B='Y12')
        self.button_1 = 'Y1'
        self.button_2 = 'Y2'
        self.button_3 = 'Y3'
        self.button_4 = 'Y4'
        self.button_5 = 'Y5'
        self.button_6 = 'Y6'
        self.LED_1 = 'Y7'
        self.LED_2 = 'Y8'
        self.LED_3 = 'Y9'
        self.LED_4 = 'Y10'
        self.LED_5 = 'Y11'
        self.LED_6 = 'Y12'
        self.BNC_1 = 'X7'
        self.BNC_2 = 'X8'
        self.DAC_1 = 'X5'
        self.DAC_2 = 'X6'
        # Set default pullup/pulldown resistors.
        hardware.default_pulls = {self.button_1:  pyb.Pin.PULL_DOWN,
                                  self.button_2:  pyb.Pin.PULL_DOWN,
                                  self.button_3:  pyb.Pin.PULL_DOWN,
                                  self.button_4:  pyb.Pin.PULL_DOWN,
                                  self.button_5:  pyb.Pin.PULL_DOWN,
                                  self.button_6:  pyb.Pin.PULL_DOWN}