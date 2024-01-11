from pyControl.hardware import Port


class Breakout_1_2:
    def __init__(self):
        # Inputs and outputs.
        self.port_1 = Port(DIO_A="X1", DIO_B="X2", POW_A="Y7", POW_B="Y8", POW_C="Y11", UART=4)
        self.port_2 = Port(DIO_A="Y3", DIO_B="Y4", POW_A="X4", POW_B="X18", POW_C="Y12")
        self.port_3 = Port(DIO_A="X9", DIO_B="X10", POW_A="X7", POW_B="X19", DIO_C="X5", DAC=1, I2C=1, UART=1)
        self.port_4 = Port(DIO_A="Y9", DIO_B="Y10", POW_A="X8", POW_B="X20", DIO_C="X6", DAC=2, I2C=2, UART=3)
        self.port_5 = Port(DIO_A="Y5", DIO_B="Y6", POW_A="X21", POW_B="X22")
        self.port_6 = Port(DIO_A="X3", DIO_B="X11", POW_A="Y1", POW_B="Y2")
        self.BNC_1 = "X12"
        self.BNC_2 = "X11"
        self.DAC_1 = "X5"
        self.DAC_2 = "X6"
        self.button = "X17"
