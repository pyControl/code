import pyb
from . import framework as fw

# ----------------------------------------------------------------------------------------
# Variables.
# ----------------------------------------------------------------------------------------

digital_inputs  = []  # All Digital_input objects.

active_inputs = [] # Digital input objects used by current state machines.

digital_outputs = []  # All Digital_output objects.

available_timers = [7,8,9,10,11,12,13,14] # Hardware timers not in use by other fuctions.

default_pull = {'down': [], # Used when Mainboards are initialised to specify 
                'up'  : []} # default pullup or pulldown resistors for pins.

initialised = False # Set to True once hardware has been intiialised.

# ----------------------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------------------

def initialise():
    # Puts those Digital_inputs that are used by current state machines
    # into active_inputs list and assigns their IDs.
    global active_inputs, initialised
    active_inputs = [digital_input for digital_input in digital_inputs
                     if digital_input._set_event_IDs()]
    for i, digital_input in enumerate(active_inputs):
        digital_input.ID = i  
    initialised = True   

def reset():
    # Reset state of inputs and turn off outputs.
    for digital_input in active_inputs:
        digital_input.reset()  
    off()

def off():
    # Turn of all digital outputs.
    for digital_output in digital_outputs:
        digital_output.off()

# ----------------------------------------------------------------------------------------
# Digital Input
# ----------------------------------------------------------------------------------------

class Digital_input():
    def __init__(self, pin, rising_event = None, falling_event = None, debounce = 5,
                 decimate = False, pull = None):
        # Digital_input class provides functionallity to generate framework events when a
        # specified pin on the Micropython board changes state. Seperate events can be
        # specified for rising and falling edges. 
        # By defalt debouncing is used to prevent multiple events being triggered very 
        # close together in time if the edges are not clean.  The debouncing method used
        # ensures that transient inputs shorter than the debounce duration still generate 
        # rising and faling edges.  Debouncing incurs some overheads so should be turned
        # off for inputs with clean edges and high event rates.
        # Setting the decimate argument to an integer n causes only every n'th input to 
        # generate an event.  Decimate can be used only with debouncing off and an event 
        # specified for a single edge.
        # Arguments:
        # pin           - micropython pin to use
        # rising_event  - Name of event triggered on rising edges.
        # falling_event - Name of event triggered on falling edges.
        # debounce      - Minimum time interval between events (ms), 
        #                 set to False to deactive debouncing.
        # decimate      - set to n to only generate 1 event for every n input pulses.
        # pull          - used to enable internal pullup or pulldown resitors. 
        if decimate:
            assert isinstance(decimate, int), '! Decimate argument must be integer or False'
            assert not (rising_event and falling_event), '! Decimate can only be used with single edge'
            debounce = False
        if pull is None: # No pullup or pulldown resistor specified, use default.
            if pin in default_pull['up']:
                pull = pyb.Pin.PULL_UP
            elif pin in default_pull['down']:
                pull = pyb.Pin.PULL_DOWN
            else:
                pull = pyb.Pin.PULL_NONE
        elif pull == 'up':
            pull = pyb.Pin.PULL_UP
        elif pull == 'down':
            pull = pyb.Pin.PULL_DOWN
        self.pull = pull
        self.pin = pyb.Pin(pin, pyb.Pin.IN, pull = pull)
        self.rising_event = rising_event
        self.falling_event = falling_event
        self.debounce = debounce     
        self.decimate = decimate
        self.ID = None # Overwritten by initialise()
        digital_inputs.append(self)

    def _set_event_IDs(self):
        # Set event codes for rising and falling events.  If neither rising or falling event 
        # is used by framework, the interrupt is not activated. Returns boolean indicating
        # whether input is active.
        self.rising_event_ID  = fw.events[self.rising_event ] if self.rising_event  in fw.events else False
        self.falling_event_ID = fw.events[self.falling_event] if self.falling_event in fw.events else False
        if not (self.rising_event_ID or self.falling_event_ID):
            return False # Input not used by current state machines.
        # Setup interrupts.
        if self.debounce or (self.rising_event_ID and self.falling_event_ID):
            pyb.ExtInt(self.pin, pyb.ExtInt.IRQ_RISING_FALLING, self.pull, self._ISR)
            self.use_both_edges = True
        else:
            self.use_both_edges = False
            if self.rising_event_ID:
                pyb.ExtInt(self.pin, pyb.ExtInt.IRQ_RISING, self.pull, self._ISR)
                self.pin_state = True
            else:
                pyb.ExtInt(self.pin, pyb.ExtInt.IRQ_FALLING, self.pull, self._ISR)
                self.pin_state = False
        return True

    def _ISR(self, line):
        # Interrupt service routine called on pin change.
        if self.debounce_active:
                return # Ignore interrupt as too soon after previous interrupt.
        if self.decimate:
            self.decimate_counter = (self.decimate_counter+1) % self.decimate
            if not self.decimate_counter == 0:
                return # Ignore input due to decimation.
        self.interrupt_timestamp = fw.current_time
        if self.debounce: # Digital input uses debouncing.
            self.debounce_active = True
            self.pin_state = not self.pin_state
        elif self.use_both_edges:
            self.pin_state = self.pin.value()
        self.interrupt_triggered = True # Set tag on Digital_input.
        fw.interrupts_waiting    = True # Set tag on framework (common to all Digital_inputs).

    def _process_interrupt(self):
        # Put apropriate event for interrupt in event queue.
        self.interrupt_triggered = False
        self._publish_if_edge_has_event(self.interrupt_timestamp)
        if self.debounce: # Set timer to deactivate debounce in self.debounce milliseconds.
            fw.timer.set(self.debounce, (fw.debounce_evt, self.ID))

    def _deactivate_debounce(self):
        # Called when debounce timer elapses, deactivates debounce and 
        # if necessary publishes event for edge missed during debounce.
        if not self.pin_state == self.pin.value(): # An edge has been missed.  
            self.pin_state = not self.pin_state  
            self._publish_if_edge_has_event(fw.current_time)
        self.debounce_active = False

    def _publish_if_edge_has_event(self, timestamp):
        # Publish event if detected edge has event ID assigned.
        if self.pin_state and self.rising_event_ID:          # Rising edge.
            fw.event_queue.put((self.rising_event_ID, timestamp))
        elif (not self.pin_state) and self.falling_event_ID: # Falling edge.
            fw.event_queue.put((self.falling_event_ID, timestamp))

    def value(self):
        # Return state of the input. 
        return self.pin.value()

    def reset(self): # Reset state of input, called at beginning of run.
        self.interrupt_triggered = False  # Flag to tell framework to run _process_interrupt.
        self.debounce_active = False      # Set True when pin is ignoring inputs due to debounce.
        if self.use_both_edges:
            self.pin_state = self.pin.value()
        self.interrupt_timestamp = 0
        self.decimate_counter = -1

# ----------------------------------------------------------------------------------------
# Digital Output.
# ----------------------------------------------------------------------------------------

class Digital_output():

    def __init__(self, pin, inverted=False, pulse_enabled=False):
        self.pin = pyb.Pin(pin, pyb.Pin.OUT_PP)  # Micropython pin object.
        self.inverted = inverted # Set True for inverted output.
        self.timer = False # Replaced by timer object if pulse enabled.
        self.off()
        if pulse_enabled:
            self.enable_pulse()
        digital_outputs.append(self)

    def on(self):
        self.pin.value(not self.inverted)
        self.state = True

    def off(self):
        if self.timer:
            self.timer.deinit()
        self.pin.value(self.inverted)
        self.state = False

    def toggle(self, t=None): # Unused argument is for compatibility with timer callback.
        if self.state:
            self.pin.value(self.inverted)
        else:
            self.pin.value(not self.inverted)
        self.state = not self.state  

    def enable_pulse(self): # Setup a hardware timer to allow pulsed output  
        self.timer = pyb.Timer(available_timers.pop())

    def pulse(self, freq): # Turn on squarewave output with specified frequency. 
        self.on()
        self.timer.init(freq=freq*2)
        self.timer.callback(self.toggle)

# ----------------------------------------------------------------------------------------
# Digital Outputs.
# ----------------------------------------------------------------------------------------

class Digital_output_group():
    # Grouping of Digital_output objects with methods for turning on or off together.
    def __init__(self, digital_outputs):
        self.digital_outputs = digital_outputs

    def on(self):
        for digital_output in self.digital_outputs:
            digital_output.on()

    def off(self):
        for digital_output in self.digital_outputs:
            digital_output.off()

# ----------------------------------------------------------------------------------------
# Port
# ----------------------------------------------------------------------------------------

class Port():
    # Class representing one RJ45 behavioural hardware port.
    def __init__(self, DIO_A, DIO_B, POW_A, POW_B, 
                 DIO_C=None, POW_C=None, DAC=None, I2C=None):
        self.DIO_A = DIO_A
        self.DIO_B = DIO_B
        self.DIO_C = DIO_C
        self.POW_A = POW_A
        self.POW_B = POW_B
        self.POW_C = POW_C
        self.DAC   = DAC
        self.I2C   = I2C

# ----------------------------------------------------------------------------------------
# Mainboard
# ----------------------------------------------------------------------------------------

class Mainboard():
    # Parent class for devboard and breakout boards.
    
    def set_pull_updown(self, pull): # Set default pullup/pulldown resistors.
        default_pull.update(pull)