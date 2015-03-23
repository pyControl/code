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

# ----------------------------------------------------------------------------------------
# boxIO
# ----------------------------------------------------------------------------------------

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

    def digital_read(self, pin, force_read = True):
        if force_read: # Read input state from MCP rather than using stored value from previous read.   
            self.input_state = i2c.mem_read(1, self.addr, GPIOA, timeout=5000)[0]
        return bool(self.input_state & (1 << pin))

    def process_interrupt(self):
        # Evaluate which active pins have changed state and publish required events.
        self.interrupt_timestamp = self.interrupt_timestamp - self.pc.start_time
        self.interrupt_triggered = False
        new_input_state = i2c.mem_read(1, self.addr, GPIOA, timeout=5000)[0]
        changed_pins = new_input_state ^ self.input_state
        for pin in self.active_pins:
            pin_bit = 1 << pin
            if changed_pins & pin_bit: # Pin has changed.
                rising_event_ID, falling_event_ID, machine_ID = self.active_pins[pin]
                if new_input_state & pin_bit: # Pin is high - rising change.
                    if rising_event_ID:
                       self.pc.publish_event((machine_ID,  rising_event_ID, self.interrupt_timestamp))
                else:                         # Pin is low - falling change.
                    if falling_event_ID:
                        self.pc.publish_event((machine_ID, falling_event_ID, self.interrupt_timestamp))
        self.input_state = new_input_state 
        

# ----------------------------------------------------------------------------------------
# Digital Input
# ----------------------------------------------------------------------------------------

class Digital_input():
    def __init__(self, boxIO, pin, rising = None, falling = None):
        self.pin = pin
        self.boxIO = boxIO
        self.rising_event = rising
        self.falling_event = falling

    def set_events(self, rising, falling):
        # Set event names for rising and falling edges.
        self.rising_event = rising
        self.falling_event = falling

    def set_machine(self, state_machine):
        # Attach digital input to state machine.
        if self.rising_event in state_machine.events:
            rising_event_ID  = state_machine.events[self.rising_event]
        else:
            rising_event_ID = None
        if self.falling_event in state_machine.events:
            falling_event_ID = state_machine.events[self.falling_event]
        else:
            falling_event_ID = None
        self.boxIO.active_pins[self.pin] = (rising_event_ID, falling_event_ID, state_machine.ID) 

    def __call__(self, force_read = False):
        # Calling Digital_input object returns state of input. 
        return self.boxIO.digital_read(self.pin, force_read)

# ----------------------------------------------------------------------------------------
# Digital Output.
# ----------------------------------------------------------------------------------------

class Digital_output():
    def __init__(self, boxIO, pin):
        self.pin = pin
        self.boxIO = boxIO
        self.state = False

    def on(self):
         self.boxIO.digital_write(self.pin, True)
         self.state = True

    def off(self):
         self.boxIO.digital_write(self.pin, False)
         self.state = False

    def toggle(self):
        if self.state:
            self.off()
        else:
            self.on()    

 
# ----------------------------------------------------------------------------------------
# Poke
# ----------------------------------------------------------------------------------------

class Poke():
    def __init__(self, boxIO, port, rising = None, falling = None, rising_B = None, falling_B = None):
 

        self.boxIO = boxIO

        port_pins = boxIO.ports[port]

        self.LED     = Digital_output(boxIO, port_pins['POW_B'])
        self.SOL     = Digital_output(boxIO, port_pins['POW_A'])
        self.input_A = Digital_input( boxIO, port_pins['DIO_A'])
        self.input_B = Digital_input( boxIO, port_pins['DIO_B'])

        self.set_events(rising, falling, rising_B, falling_B)

    def set_events(self, rising = None, falling = None,
                         rising_B = None, falling_B = None):
        # Assign event names to poke input pins.
        self.input_A.set_events(rising, falling)
        self.input_B.set_events(rising_B, falling_B)


    def set_machine(self, state_machine):
        # Assigns poke to state machine.  For each input with an event name assigned, adds appropriate event codes, 
        #  and state_maching ID to boxIO object active_pins dictionary.
        self.input_A.set_machine(state_machine)
        self.input_B.set_machine(state_machine)

    def get_state(self):
        return self.input_A()

# ----------------------------------------------------------------------------------------
# Hardware collections.
# ----------------------------------------------------------------------------------------

class Box():

    def __init__(self, PyControl, addr = 0x20, int_pin = 'X1'):
        
        self.boxIO = BoxIO(PyControl, addr, int_pin)

        # Instantiate components.
        self.left_poke   = Poke(self.boxIO, port = 1, rising = 'left_poke', falling = 'left_poke_out')
        self.center_poke = Poke(self.boxIO, port = 2, rising = 'high_poke', rising_B = 'low_poke')
        self.right_poke  = Poke(self.boxIO, port = 3, rising = 'right_poke', falling = 'right_poke_out')
        self.button      = Digital_input(self.boxIO, pin = 3, rising = 'session_startstop')
        self.houselight  = Digital_output(self.boxIO, pin = 3)

        self.all_inputs = [self.left_poke, self.center_poke, self.right_poke, self.button]

    def set_machine(self, state_machine):
        for i in self.all_inputs:
            i.set_machine(state_machine)

    def off(self):
        self.boxIO.outputs_off()
