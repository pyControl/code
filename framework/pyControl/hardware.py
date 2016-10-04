import pyb
from . import framework as fw

# ----------------------------------------------------------------------------------------
# Variables.
# ----------------------------------------------------------------------------------------

digital_inputs = []  # List of all Digital_input objects.

digital_outputs = []  # List of all Digital_output objects.

hardware_definition = None  # Hardware definition object.

# ----------------------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------------------


def initialise(hwd=None):
    # Attempt to import hardware_definition if not supplied as argument.
    # Inserts hardware_definition module into state machine definition namespaces.
    # Sets event IDs on digital inputs from framework events dictionary and remove digital
    # inputs that are not used by state machine to reduce overheads.
    global hardware_definition, digital_inputs
    if not hardware_definition:
        try:
            import hardware_definition
            for state_machine in fw.state_machines:
                state_machine.smd.hw = hardware_definition
        except ImportError:
            hardware_definition = None
    digital_inputs = [digital_input for digital_input in digital_inputs
                      if digital_input._set_event_IDs()]


def reset():
    # Called before each run to reset digital inputs.
    for digital_input in digital_inputs:
        digital_input.reset()


def off():
    # Turn of all digital outputs.
    for digital_output in digital_outputs:
        digital_output.off()


def connect_device(device, connector, pull=None):
    if pull:
        device.connect(connector, pull)
    else:
        device.connect(connector)

# ----------------------------------------------------------------------------------------
# Digital Input
# ----------------------------------------------------------------------------------------


class Digital_input(object):

    counter = 3 # do not interfer with built-in events

    def get_uid(self):
      Digital_input.counter += 1
      print("next_uid: ", Digital_input.counter)
      return Digital_input.counter

    def __init__(self, rising_event=None, falling_event=None, debounce=5):
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
        if rising_event:
            self.rising_event = rising_event
        else:
            self.rising_event = self.get_uid()

        if falling_event:
            self.falling_event = falling_event
        else:
            self.falling_event = self.get_uid()

        self.debounce = debounce
        self.ID = len(digital_inputs)  # Index in digital inputs list.
        digital_inputs.append(self)

    def connect(self, pin, pull=pyb.Pin.PULL_NONE):
        # Specify the Digital_input pin and optional pullup or pulldown resistor.
        self.pin = pyb.Pin(pin, pyb.Pin.IN, pull=pull)
        self.pull = pull

    def _set_event_IDs(self):
        # Set event codes for rising and falling events.  If neither rising or falling event
        # is used by framework, the interrupt is not activated. Returns boolean indicating
        # whether input is active.
        if self.rising_event in fw.events:
            self.rising_event_ID = fw.events[self.rising_event]
        else:
            self.rising_event_ID = None
        if self.falling_event in fw.events:
            self.falling_event_ID = fw.events[self.falling_event]
        else:
            self.falling_event_ID = None
        if self.rising_event_ID or self.falling_event_ID:
            print('rising_event_ID: ', self.rising_event_ID)
            print('falling_event_ID: ', self.falling_event_ID)
            print('pin: ', self.pin)
            pyb.ExtInt(self.pin, pyb.ExtInt.IRQ_RISING_FALLING, self.pull, self._ISR)
            self.reset()
            return True
        else:
            return False

    def _ISR(self, line):
        # Interrupt service routine called on pin change.
        if self.debounce_active:
            return  # Ignore interrupt as too soon after previous interrupt.
        self.interrupt_timestamp = pyb.millis()
        if self.debounce:  # Digitial input uses debouncing.
            self.pin_state = not self.pin_state
            self.debounce_active = True
        else:
            self.pin_state = self.pin.value()
        self.interrupt_triggered = True  # Set tag on Digital_input.
        fw.interrupts_waiting = True  # Set tag on framework (common to all Digital_inputs).

    def _process_interrupt(self):
        # Put apropriate event for interrupt in event queue.
        timestamp = self.interrupt_timestamp - fw.start_time
        self.interrupt_triggered = False
        self._publish_if_edge_has_event(timestamp)
        if self.debounce:  # Set timer to deactivate debounce in self.debounce milliseconds.
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
            fw.event_queue.put((self.rising_event_ID, timestamp))
        elif (not self.pin_state) and self.falling_event_ID:  # Falling edge.
            fw.event_queue.put((self.falling_event_ID, timestamp))

    def value(self):
        # Return state of the input.
        return self.pin.value()

    def reset(self):  # Reset state of input, called at beginning of run.
        self.interrupt_triggered = False  # Flag to tell framework to run _process_interrupt.
        self.debounce_active = False      # Set True when pin is ignoring inputs due to debounce.
        self.pin_state = self.pin.value()
        self.interrupt_timestamp = 0

# ----------------------------------------------------------------------------------------
# Digital Output.
# ----------------------------------------------------------------------------------------


class Digital_output(object):

    def __init__(self, inverted=False):
        self.inverted = inverted  # Set True for inverted output.

    def connect(self, pin):
        self.pin = pyb.Pin(pin, pyb.Pin.OUT_PP)  # Micropython pin object.
        self.state = False
        digital_outputs.append(self)
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
# Digital Outputs.
# ----------------------------------------------------------------------------------------


class Digital_output_group(object):
    # Grouping of Digital_output objects with methods for turning on or off together.

    def __init__(self, digital_outputs):
        self.digital_outputs = digital_outputs

    def on(self):
        for digital_output in self.digital_outputs:
            digital_output.on()

    def off(self):
        for digital_output in self.digital_outputs:
            digital_output.off()
