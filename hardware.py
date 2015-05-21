import pyb

# ----------------------------------------------------------------------------------------
# Digital Input
# ----------------------------------------------------------------------------------------

class Digital_input():
    def __init__(self, pyControl, pin, rising = None, falling = None,
                 debounce = 20, pull = pyb.Pin.PULL_DOWN):
        # Rising and falling event names are specified when digital input is initialised,
        # these are converted to event IDs when the Digital_input is assigned to a 
        #state machine.
        self.rising_event = rising
        self.falling_event = falling
        self.debounce = debounce             # Minimum interval between interrupts.
        self.pc = pyControl                  # Pointer to framework.
        self.pc.register_hardware(self)      # Register digital input with framwork.

        self.pin = pyb.Pin(pin, pyb.Pin.IN)  # Micropython pin object.
        pyb.ExtInt(pin, pyb.ExtInt.IRQ_RISING_FALLING, pull, self._ISR) # Configure interrupt on pin.
        self.interrupt_timestamp = 0         # Time of interrupt occured.
        self.interrupt_rising = False        # True for rising interrupt, false for falling interrupt.
        self.reset()

    def set_machine(self, state_machine):
        # Attach digital input to state machine.
        self.machine_ID = state_machine.ID
        if self.rising_event in state_machine.events:
            self.rising_event_ID  = state_machine.events[self.rising_event]
        else:
            self.rising_event_ID = None
        if self.falling_event in state_machine.events:
            self.falling_event_ID = state_machine.events[self.falling_event]
        else:
            self.falling_event_ID = None

    def _ISR(self, line):
        # Interrupt service routing called on pin change.
        self.interrupt_timestamp = pyb.millis()
        if self.debounce and ((self.interrupt_timestamp - self.prev_timestamp) < 
                              self.debounce): # Rollover safe?
           return # Ignore interrupt as to soon after previous interrupt.
        if self.pin.value() and self.rising_event_ID: # Pin is high, rising event.
            self.interrupt_rising = True
        elif not self.pin.value() and self.falling_event_ID: # Pin is low, falling event.
            self.interrupt_rising = False
        else:
            return # Ignore interrupt as no event_ID assigned to edge.
        self.prev_timestamp = self.interrupt_timestamp
        self.interrupt_triggered = True    # Set tag on Digital_input.
        self.pc.interrupts_waiting = True  # Set tag on framework (common to all Digital_inputs).

    def _process_interrupt(self):
        # Put apropriate event for interrupt in event queue.
        timestamp = self.interrupt_timestamp - self.pc.start_time
        self.interrupt_triggered = False
        if self.interrupt_rising:
            self.pc.publish_event((self.machine_ID, self.rising_event_ID, timestamp))
        else:
            self.pc.publish_event((self.machine_ID, self.falling_event_ID, timestamp))

    def __call__(self, force_read = False):
        # Calling Digital_input object returns state of the input. 
        return self.pin.value()

    def reset(self): # Called at begining of run.
        self.prev_timestamp = 0                 # Time when previous interrupt occured.
        self.interrupt_triggered = False        # Flag to tell framework to run _process_interrupt.
        


# ----------------------------------------------------------------------------------------
# Digital Output.
# ----------------------------------------------------------------------------------------

class Digital_output():
    def __init__(self, pin, inverted = False):
        self.pin = pyb.Pin(pin, pyb.Pin.OUT_PP)  # Micropython pin object.
        self.state = False
        self.inverted = inverted # Set True for inverted output.
        self.off()

    def on(self):
         self.pin.value(not self.inverted)
         self.state = True

    def off(self):
         self.pin.value(self.inverted)
         self.state = False

    def toggle(self):
        if self.state:
            self.off()
        else:
            self.on()    


# ----------------------------------------------------------------------------------------
# Poke
# ----------------------------------------------------------------------------------------

ports = {1: {'DIO_A': 'Y1',   # Pin mappings for pyDev development board.
             'DIO_B': 'Y4',
             'POW_A': 'Y8',
             'POW_B': 'Y7'},

         2: {'DIO_A': 'Y2',
             'DIO_B': 'Y5',
             'POW_A': 'Y10',
             'POW_B': 'Y9'},

         3: {'DIO_A': 'Y3',
             'DIO_B': 'Y6',
             'POW_A': 'Y12',
             'POW_B': 'Y11'}}

class Poke():
    def __init__(self, pyControl, port, rising = None, falling = None, rising_B = None, falling_B = None):

        self.SOL     = Digital_output(ports[port]['POW_A'])
        self.LED     = Digital_output(ports[port]['POW_B'])
        self.input_A = Digital_input(pyControl, ports[port]['DIO_A'], rising,   falling)
        self.input_B = Digital_input(pyControl, ports[port]['DIO_B'], rising_B, falling_B)

    def set_machine(self, state_machine):
        # Assigns poke to state machine.  For each input with an event name assigned, adds appropriate event codes, 
        #  and state_maching ID to boxIO object active_pins dictionary.
        self.input_A.set_machine(state_machine)
        self.input_B.set_machine(state_machine)

    def get_state(self):
        return self.input_A()

    def off(self): # Turn off all outputs.
        self.SOL.off()
        self.LED.off()

# ----------------------------------------------------------------------------------------
# Hardware collections.
# ----------------------------------------------------------------------------------------

class Box():

    def __init__(self, pyControl):

        # Instantiate components.
        self.left_poke   = Poke(pyControl, port = 1, rising = 'left_poke', falling = 'left_poke_out')
        self.center_poke = Poke(pyControl, port = 2, rising = 'high_poke', rising_B = 'low_poke')
        self.right_poke  = Poke(pyControl, port = 3, rising = 'right_poke', falling = 'right_poke_out', rising_B = 'session_startstop')
        self.houselight  = self.center_poke.SOL

        self.all_inputs = [self.left_poke, self.center_poke, self.right_poke]


    def set_machine(self, state_machine):
        for i in self.all_inputs:
            i.set_machine(state_machine)

    def reset(self):
        for i in self.all_inputs:
            i.reset()

    def off(self): # Turn off all outputs.
        for o in [self.left_poke, self.right_poke, self.center_poke]:
            o.off()
