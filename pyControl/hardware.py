import pyb
from . import framework as fw

# ----------------------------------------------------------------------------------------
# Variables.
# ----------------------------------------------------------------------------------------

digital_inputs  = []  # List of all Digital_input objects.

digital_outputs = []  # List of all Digital_output objects.

hardware_definition = None  # Hardware definition object.

# ----------------------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------------------

def initialise(hwd = None):
    # Attempt to import hardware_definition if not supplied as argument. 
    # Insert hardware_definition module into state machine definition namespaces.
    # Set event IDs on digital inputs from framework events dictionary.    
    print('importing hardware_definition')
    global hardware_definition
    if not hardware_definition:
        try:
            import hardware_definition
        except ImportError:
            hardware_definition = None
    for state_machine in fw.state_machines:
        state_machine.smd.hw = hardware_definition
    for digital_input in digital_inputs:
        digital_input._set_event_IDs()

def reset():
    # Called before each run to reset digital inputs.
    for digital_input in digital_inputs:
        digital_input.reset()

def off():
    # Turn of all digital outputs.
    for digital_output in digital_outputs:
        digital_output.off()

def connect_device(device, connector, pull = pyb.Pin.PULL_NONE):
    device.connect(connector, pull)

# ----------------------------------------------------------------------------------------
# Digital Input
# ----------------------------------------------------------------------------------------

class Digital_input():
    def __init__(self, rising_event = None, falling_event = None, debounce = 5):
        # Digital_input class provides functionallity to generate framework events when a
        # specified pin on the Micropython board changes state. Seperate events can be
        # specified for rising and falling pin changes. The event names associated with
        # rising and falling edges are specified when Digital_input is initialised using 
        # the rising and falling arguments.  These are converted to the appropriate event
        # IDs when the Digital_input is registered with the framework.
        # By defalt debouncing is used to prevent multiple events being triggered very 
        # close together in time if the edges are not clean.  The debouncing method used
        # ensures that transient inputs shorter than the debounce duration still generate 
        # rising and faling edges.  
        # Arguments:
        # rising_event  - Name of event triggered on rising edges.
        # falling_event - Name of event triggered on falling edges.
        # debounce      - Minimum time interval between events (ms), 
        #                 set to False to deactive debouncing.
        self.rising_event = rising_event
        self.falling_event = falling_event
        self.debounce = debounce     
        self.ID = len(digital_inputs) # Index in digital inputs list.
        digital_inputs.append(self)

    def connect(self, pin, pull = pyb.Pin.PULL_NONE): 
        # Specify the Digital_input pin and optional pullup or pulldown resistor.  
        self.pin = pyb.Pin(pin, pyb.Pin.IN, pull = pull)
        self.pull = pull
        self.reset()

    def _set_event_IDs(self):
        # Set event codes for rising and falling events.  If neither rising or falling event 
        # is used by framework, the interrupt is not activated.
        if self.rising_event in fw.events:
            self.rising_event_ID  = fw.events[self.rising_event]
        else:
            self.rising_event_ID = None
        if self.falling_event in fw.events:
            self.falling_event_ID = fw.events[self.falling_event]
        else:
            self.falling_event_ID = None
        if self.rising_event_ID or self.falling_event_ID:
            pyb.ExtInt(self.pin, pyb.ExtInt.IRQ_RISING_FALLING, self.pull, self._ISR)

    def _ISR(self, line):
        # Interrupt service routine called on pin change.
        if self.debounce_active:
                return # Ignore interrupt as too soon after previous interrupt.
        self.interrupt_timestamp = pyb.millis()
        if self.debounce: # Digitial input uses debouncing.
            self.pin_state = not self.pin_state
            self.debounce_active = True
        else:
            self.pin_state = self.pin.value()
        self.interrupt_triggered = True # Set tag on Digital_input.
        fw.interrupts_waiting    = True # Set tag on framework (common to all Digital_inputs).

    def _process_interrupt(self):
        # Put apropriate event for interrupt in event queue.
        timestamp = self.interrupt_timestamp - fw.start_time
        self.interrupt_triggered = False
        self._publish_if_edge_has_event(timestamp)
        if self.debounce: # Set timer to deactivate debounce in self.debounce milliseconds.
            fw.timer.set(-self.ID, self.debounce) 

    def _deactivate_debounce(self):
        # Called when debounce timer elapses, deactivates debounce and 
        # if necessary publishes event for edge missed during debounce.
        if not (self.pin_state == self.pin.value()):  # An edge has been missed.
            self.pin_state = not self.pin_state
            self._publish_if_edge_has_event(fw.current_time)
        self.debounce_active = False

    def _publish_if_edge_has_event(self, timestamp):
        # Publish event if detected edge has event ID assigned.
        if self.pin_state and self.rising_event_ID:          # Rising edge.
            fw.publish_event((self.rising_event_ID, timestamp))
        elif (not self.pin_state) and self.falling_event_ID: # Falling edge.
            fw.publish_event((self.falling_event_ID, timestamp))

    def value(self):
        # Return state of the input. 
        return self.pin.value()

    def reset(self): # Reset state of input, called at beginning of run.
        self.interrupt_triggered = False  # Flag to tell framework to run _process_interrupt.
        self.debounce_active = False      # Set True when pin is ignoring inputs due to debounce.
        self.pin_state = self.pin.value()
        self.interrupt_timestamp = 0

# ----------------------------------------------------------------------------------------
# Digital Output.
# ----------------------------------------------------------------------------------------

class Digital_output():
    def __init__(self, inverted = False):
        self.inverted = inverted # Set True for inverted output.
        digital_outputs.append(self)

    def connect(self, pin):
        self.pin = pyb.Pin(pin, pyb.Pin.OUT_PP)  # Micropython pin object.
        self.state = False
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
# Double_poke
# ----------------------------------------------------------------------------------------

class Poke():
    
    def __init__(self, rising_event = None, falling_event = None, debounce = 5):
        self.SOL   = Digital_output()
        self.LED   = Digital_output()
        self.input = Digital_input(rising_event, falling_event, debounce)

    def connect(self, port, pull = pyb.Pin.PULL_NONE):
        self.SOL.connect(port['POW_A'])
        self.LED.connect(port['POW_B'])
        self.input.connect(port['DIO_A'], pull)

    def value(self):
        # Return the state of input A.
        return self.input.value()


# ----------------------------------------------------------------------------------------
# Double_poke
# ----------------------------------------------------------------------------------------

class Double_poke():
    
    def __init__(self, rising_event_A = None, falling_event_A = None,
                       rising_event_B = None, falling_event_B = None, debounce = 5):
        self.SOL     = Digital_output()
        self.LED     = Digital_output()
        self.input_A = Digital_input(rising_event_A, falling_event_A, debounce)
        self.input_B = Digital_input(rising_event_B, falling_event_B, debounce)

    def connect(self, port, pull = pyb.Pin.PULL_NONE):
        self.SOL.connect(port['POW_A'])
        self.LED.connect(port['POW_B'])
        self.input_A.connect(port['DIO_A'], pull)
        self.input_B.connect(port['DIO_B'], pull)

    def value(self):
        # Return the state of input A.
        return self.input_A.value()

# ----------------------------------------------------------------------------------------
# Board pin mapping dictionaries.
# ----------------------------------------------------------------------------------------

# These dictionaries provide pin mappings for specific boards whose schematics are
# provided in the pyControl/schematics folder.

breakout_1_0 = {'ports': {1: {'DIO_A': 'X1',   # RJ45 connector port pin mappings.
                              'DIO_B': 'X2',
                              'POW_A': 'Y4',
                              'POW_B': 'Y8'},
         
                          2: {'DIO_A': 'X3',
                              'DIO_B': 'X4',
                              'POW_A': 'Y3',
                              'POW_B': 'Y7'},
         
                          3: {'DIO_A': 'X7',
                              'DIO_B': 'X8',
                              'POW_A': 'Y2',
                              'POW_B': 'Y6'},
         
                          4: {'DIO_A': 'X12',
                              'DIO_B': 'X11',
                              'POW_A': 'Y1',
                              'POW_B': 'Y5'}},
                'BNC_1': 'Y11',      # BNC connector pins.
                'BNC_2': 'Y12',
                'DAC_1': 'X5',
                'DAC_2': 'X6',
                'button_1': 'X9',    # User pushbuttons.
                'button_2': 'X10'}

devboard_1_0 = {'ports': {1: {'DIO_A': 'Y1',   # Use buttons and LEDs to emulate breakout board ports.
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
                              'POW_B': 'Y11'}},
                'button_1': 'Y1',  # Access buttons and pins directly. 
                'button_2': 'Y2',
                'button_3': 'Y3',
                'button_4': 'Y4',
                'button_5': 'Y5',
                'button_6': 'Y6',
                'LED_1': 'Y7',
                'LED_2': 'Y8',
                'LED_3': 'Y9',
                'LED_4': 'Y10',
                'LED_5': 'Y11',
                'LED_6': 'Y12',
                'BNC_1': 'X7',     # BNC connector pins.
                'BNC_2': 'X8',
                'DAC_1': 'X5',
                'DAC_2': 'X6',
                }