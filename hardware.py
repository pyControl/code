# BoxControl MCP pin mappings.

# A0: DIO_1A  # Port A mappings
# A1: DIO_2A
# A2: DIO_3A
# A3: DIO_4A
# A4: DIO_1B
# A5: DIO_2B
# A6: DIO_3B
# A7: DIO_4B

# B0: SOL_1  # Port A mappings
# B1: SOL_2
# B2: SOL_3
# B3: SOL_4
# B4: LED_1
# B5: LED_2
# B6: LED_3
# B7: LED_4

import pyb
from pyb import I2C

i2c = I2C(1)                          # create on bus 1
i2c.init(I2C.MASTER, baudrate=400000) # init as a master

# Register addresses on MCP23017

IODIRA    = 0x00   # Port A input / output direction register.
IODIRB    = 0x01   # Port B input / output direction register.
GPIOA     = 0x12   # Port A state register.
GPIOB     = 0x13   # Port B state register
GPINTENA  = 0x04   # Port A interrupt on change enable register.
IOCONA    = 0x0A   # Port A configuration register.


class BoxIO():

    def __init__(self, addr = 0x20, int_pin = 'X1'):

        self.addr = 0x20     # Device address

        i2c.mem_write(0x00, self.addr, IODIRB, timeout=5000)   # Set all port B pins as outputs.
        i2c.mem_write(2, self.addr, IOCONA, timeout=5000)      # Set interrupts active high
        i2c.mem_write(0xFF, self.addr, GPINTENA, timeout=5000) # Turn on interrupts for port A

        # Configure pyboard interrupt
        self.extint = pyb.ExtInt(int_pin, pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_NONE, self.ISR)

        self.input_state  = i2c.mem_read(1, self.addr, GPIOA, timeout=5000)[0] # Read current state of inputs.
        self.output_state = 0
        i2c.mem_write(self.output_state, self.addr, GPIOB, timeout=5000)    # Set all output lines low.

        self.ports{ 1: {'DIO_A': 0,
                        'DIO_B': 4,
                        'ULN_A': 0,
                        'ULN_B': 4}

                    2: {'DIO_A': 1,
                        'DIO_B': 5,
                        'ULN_A': 1,
                        'ULN_B': 5}

                    3: {'DIO_A': 2,
                        'DIO_B': 6,
                        'ULN_A': 2,
                        'ULN_B': 6}

                    4: {'DIO_A': 3,
                        'DIO_B': 7,
                        'ULN_A': 3,
                        'ULN_B': 7}}      


    def ISR(self, line):
        print('Interrupt!')

    def digital_write(self, pin, value):
        if value:  # Set pin high
            self.output_state = self.output_state | (1 << pin)
        else:  # Set pin low
            self.output_state = self.output_state & ~(1 << pin)
        i2c.mem_write(self.output_state, self.addr, GPIOB, timeout=5000)

    def digital_read(self, pin):   
        self.input_state = i2c.mem_read(1, self.addr, GPIOA, timeout=5000)[0]
        return bool(self.input_state & (1 << pin))

    def changed_pins(self):
        new_input_state = i2c.mem_read(1, self.addr, GPIOA, timeout=5000)[0]
        changed_pins = new_input_state ^ self.input_state
        for pin in range(8):
            if changed_pins & (1 << pin):
                pin_state = bool(new_input_state & (1 << pin))
                print('Pin {} changed, now: {}'.format(pin, pin_state))
        self.input_state = new_input_state

class poke():
    def __init__(self, boxIO, signal,  port = None, LED_pin = None,
                 SOL_pin = None, sig_pin = None):
    
        self.boxIO = boxIO
        if port:
            self.LED_pin = port['ULN_B']
            self.SOL_pin = port['ULN_A']
            self.sig_pin = port[DIO_A]
        else:
            self.LED_pin = LED_pin
            self.SOL_pin = SOL_pin
            self.sig_pin = sig_pin

        self.LED_off()
        self.SOL_off()

        # Interrupt setup code here.

    def LED_on():
        boxIO.digital_write(self.LED_pin, True)
        self.LED_state = True

    def LED_off():
        boxIO.digital_write(self.LED_pin, False)
        self.LED_state = False

    def SOL_on():
        boxIO.digital_write(self.SOL_pin, True)
        self.SOL_state = True

    def SOL_off():
        boxIO.digital_write(self.SOL_pin, False)
        self.SOL_state = False