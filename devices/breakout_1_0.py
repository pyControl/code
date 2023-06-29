from pyControl.hardware import Port


class Breakout_1_0:
    def __init__(self):
        # Inputs and outputs.

        # Jumper required to use either DAC/DIO_C or POW_C.
        self.port_1 = Port(DIO_A="X1", DIO_B="X2", DIO_C="X5", POW_A="Y8", POW_B="Y4", POW_C="Y2", DAC=1, UART=4)

        # Jumper required to use either DAC or POW_C.
        self.port_2 = Port(DIO_A="X3", DIO_B="X4", DIO_C="X6", POW_A="Y7", POW_B="Y3", POW_C="Y1", DAC=2)

        self.port_3 = Port(DIO_A="X7", DIO_B="X8", POW_A="Y6", POW_B="Y2")
        self.port_4 = Port(DIO_A="X12", DIO_B="X11", POW_A="Y5", POW_B="Y1")
        self.BNC_1 = "Y11"
        self.BNC_2 = "Y12"
        self.DAC_1 = "X5"
        self.DAC_2 = "X6"
        self.button_1 = "X9"
        self.button_2 = "X10"
