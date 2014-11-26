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

    def __init__(self, PyControl, addr = 0x20, int_pin = 'X1'):

        # Variables----------------------------------------------------------------
        self.pc = PyControl  # Pointer to framework.
        self.addr = addr     # Device I2C address
        self.interrupt_timestamp = pyb.millis() # Time of last interrupt.
        self.interrupt_triggered = False   # Flag to tell framework to run process_interrupt.
        self.active_pins = {}  # {pin: (rising_event_ID, falling_event_ID, machine_ID)}

        # Setup.

        self.pc.register_hardware(self) # Register boxIO with framwork.

        # Configure MCP23017---------------------------------------------------------
        i2c.mem_write(0x00, self.addr, IODIRB, timeout=5000)   # Set all port B pins as outputs.
        i2c.mem_write(2, self.addr, IOCONA, timeout=5000)      # Set interrupts active high
        i2c.mem_write(0xFF, self.addr, GPINTENA, timeout=5000) # Turn on interrupts for port A
        self.extint = pyb.ExtInt(int_pin, pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_NONE, self.ISR)
        self.input_state  = i2c.mem_read(1, self.addr, GPIOA, timeout=5000)[0] # Read current state of inputs.
        self.outputs_off()

        # Mapping of MCP pins to RJ45 ports---------------------------------------

        self.ports = { 1: {'DIO_A': 0,  
                           'DIO_B': 4,
                           'POW_A': 0,
                           'POW_B': 4},

                       2: {'DIO_A': 1,
                           'DIO_B': 5,
                           'POW_A': 1,
                           'POW_B': 5},

                       3: {'DIO_A': 2,
                           'DIO_B': 6,
                           'POW_A': 2,
                           'POW_B': 6},

                       4: {'DIO_A': 3,
                           'DIO_B': 7,
                           'POW_A': 3,
                           'POW_B': 7}}      


    def ISR(self, line):
        self.interrupt_triggered = True    # Set tag on boxIO object (unique for each boxIO).
        self.pc.interrupts_waiting = True  # Set tag on framework (common to all boxIOs).
        self.interrupt_timestamp = pyb.millis()

    def enable_interrupts(self):
        self.extint.enable()

    def disable_interrupts(self):
        self.extint.disable()

    def outputs_off(self):
        # Set all output lines low.
        self.output_state = 0
        i2c.mem_write(self.output_state, self.addr, GPIOB, timeout=5000)   
        
    def digital_write(self, pin, value):
        if value:  # Set pin high
            self.output_state = self.output_state | (1 << pin)
        else:  # Set pin low
            self.output_state = self.output_state & ~(1 << pin)
        i2c.mem_write(self.output_state, self.addr, GPIOB, timeout=5000)

    def digital_read(self, pin):   
        self.input_state = i2c.mem_read(1, self.addr, GPIOA, timeout=5000)[0]
        return bool(self.input_state & (1 << pin))

    def process_interrupt(self):
        # Evaluate which active pins have changed state and publish required events.
        self.interrupt_triggered = False
        new_input_state = i2c.mem_read(1, self.addr, GPIOA, timeout=5000)[0]
        changed_pins = new_input_state ^ self.input_state
        for pin in self.active_pins:
            pin_bit = 1 << pin
            if changed_pins & pin_bit: # Pin has changed.
                rising_event, falling_event, machine_ID = self.active_pins[pin]
                if new_input_state & pin_bit: # Pin is high - rising change.
                    if rising_event:
                       self.pc.publish_event((machine_ID,  rising_event, self.interrupt_timestamp))
                else:                         # Pin is low - falling change.
                    if falling_event:
                        self.pc.publish_event((machine_ID, falling_event, self.interrupt_timestamp))
        self.input_state = new_input_state 
        

#Class Digital_input():

class Poke():
    def __init__(self, boxIO, port):
    
        self.boxIO = boxIO

        if type(port) is int:
            port = boxIO.ports[port]
        self.LED_pin   = port['POW_B']
        self.SOL_pin   = port['POW_A']
        self.sig_pin_A = port['DIO_A']
        self.sig_pin_B = port['DIO_B']

        self.LED_off()
        self.SOL_off()

        self.events = {}  # Events published on interrupts  {pin:(rising_event_name, falling_event_name)}

    def set_events(self, rising = None, falling = None,
                         rising_B = None, falling_B = None):
        # Assign framework event to poke input pins.
        if rising or falling:
            self.events[self.sig_pin_A] = (rising, falling)  
        if rising_B or falling_B:
            self.events[self.sig_pin_B] = (rising_B, falling_B)  


    def set_machine(self, state_machine):
        for pin in self.events:
            rising_event, falling_event = self.events[pin]
            rising_event_ID  = state_machine.events[self.events[pin][0]]
            falling_event_ID = state_machine.events[self.events[pin][1]]
            self.boxIO.active_pins[pin] = (rising_event_ID, falling_event_ID, state_machine.ID)    

    def LED_on(self):
        self.boxIO.digital_write(self.LED_pin, True)
        self.LED_state = True

    def LED_off(self):
        self.boxIO.digital_write(self.LED_pin, False)
        self.LED_state = False

    def LED_toggle(self):
        if self.LED_state:
            self.LED_off
        else:
            self.LED_on

    def SOL_on(self):
        self.boxIO.digital_write(self.SOL_pin, True)
        self.SOL_state = True

    def SOL_off(self):
        self.boxIO.digital_write(self.SOL_pin, False)
        self.SOL_state = False

    def SOL_toggle(self):
        if self.SOL_state:
            self.SOL_off
        else:
            self.SOL_on

    def get_state(self, force_read = False):
        if force_read: # Read directly from MCP.
            return self.boxIO.digital_read(self.sig_pin_A)
        else: # Get stored value of MCP input state.
            return bool(self.boxIO.input_state & self.pin_bit)


