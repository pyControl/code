import pyb
from . import framework as fw

# ----------------------------------------------------------------------------------------
# Digital Input
# ----------------------------------------------------------------------------------------

class Digital_input():
    def __init__(self, pin, rising = None, falling = None,
                 debounce = 10, pull = pyb.Pin.PULL_DOWN):
        # Digital_input class provides functionallity to generate framework events when a
        # specified pin on the Micropython board changes state. Seperate events can be
        # specified for rising and falling pin changes. The event names associated with
        # rising and falling edges are specified when Digital_input is initialised,
        # these are converted to the appropriate event IDs when the Digital_input is 
        # assigned to a state machine.  By defalt debouncing is used to prevent multiple
        # events from being genrated by interrupts occuring very close together.  This is 
        # implemented by setting the debounce_active flag to true when an event is generated
        # and setting a timer to elapse after the debounce duration.  When the timer elapses,
        # the debounce_active flag is set to false, and the pin state is checked to see if 
        # has changed during the debounce period, in which case the relevent event is generated.
        # This ensures that transients which are shorter than the debounce time still generate
        # rising and falling events.
        #Arguments:
        # pin - Name of Micropython pin: e.g. 'Y1'
        # rising - Name of event triggered on rising edges.
        # falling - Name of event triggered on falling edges.
        # debounce - minimum time interval between events (ms), set to False to deactive debouncing.
        # pull - Used to enable pullup or pulldown resitors on pin.

        self.rising_event = rising
        self.falling_event = falling
        self.debounce = debounce             
        self.pin = pyb.Pin(pin, pyb.Pin.IN)  # Micropython pin object.
        pyb.ExtInt(pin, pyb.ExtInt.IRQ_RISING_FALLING, pull, self._ISR) # Configure interrupt on pin.
        self.interrupt_timestamp = 0         # Time interrupt occured.
        self.interrupt_rising = False        # True for rising interrupt, false for falling interrupt.
        self.ID = fw.register_hardware(self) # Register Digital_input with framwork.
        self.reset()

    def set_machine(self, state_machine):
        # Assign digital input to state machine.
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
        # Interrupt service routine called on pin change.
        self.pin_state = self.pin.value()
        self.interrupt_timestamp = pyb.millis()
        if self.debounce_active:
           return # Ignore interrupt as too soon after previous interrupt.
        if self.pin_state and self.rising_event_ID: # Pin is high, rising event.
            self.interrupt_rising = True
        elif not self.pin_state and self.falling_event_ID: # Pin is low, falling event.
            self.interrupt_rising = False
        else:
            return # Ignore interrupt as no event_ID assigned to edge.
        if self.debounce: 
            self.debounce_active = True
        self.interrupt_triggered = True    # Set tag on Digital_input.
        fw.interrupts_waiting    = True  # Set tag on framework (common to all Digital_inputs).

    def _process_interrupt(self):
        # Put apropriate event for interrupt in event queue.
        timestamp = self.interrupt_timestamp - fw.start_time
        self.interrupt_triggered = False
        if self.interrupt_rising:
            fw.publish_event((self.machine_ID, self.rising_event_ID, timestamp))
        else: 
            fw.publish_event((self.machine_ID, self.falling_event_ID, timestamp))
        if self.debounce:
            fw.timer.set(self.ID, self.debounce, -2) # Set timer to trigger _deactivate_debounce after self.debounce milliseconds.

    def _deactivate_debounce(self):
        # Called when debounce timer elapses, deactivates debounce state and 
        # if necessary publishes event that was missed during debounce.
        if self.interrupt_rising and (not self.pin.value()) and self.falling_event_ID: 
            # Interrupt was rising but pin is now low - falling event was missed during debounce.
            fw.publish_event((self.machine_ID, self.falling_event_ID, fw.current_time)) 
        elif (not self.interrupt_rising) and self.pin.value() and self.rising_event_ID: 
            # Interrupt was falling but pin is now high - rising event was missed during debounce.
            fw.publish_event((self.machine_ID, self.rising_event_ID, fw.current_time))
        self.debounce_active = False

    def value(self):
        # Return state of the input. 
        return self.pin.value()

    def reset(self): # Reset state of input, called at beginning of run.
        self.interrupt_triggered = False        # Flag to tell framework to run _process_interrupt.
        self.debounce_active = False            # Set true when pin is ignoring inputs due to debounce.
        self.pin_state = self.pin.value()
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

ports = {1: {'DIO_A': 'Y1',   # Pin mappings for pyControl devboard 1.0 board.
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
    def __init__(self, port, rising = None, falling = None, rising_B = None, falling_B = None, debounce = 10):

        self.SOL     = Digital_output(ports[port]['POW_A'])
        self.LED     = Digital_output(ports[port]['POW_B'])
        self.input_A = Digital_input(ports[port]['DIO_A'], rising,   falling,   debounce = debounce)
        self.input_B = Digital_input(ports[port]['DIO_B'], rising_B, falling_B, debounce = debounce)

    def set_machine(self, state_machine):
        # Assigns poke to state machine.  For each input with an event name assigned, adds appropriate event codes, 
        #  and state_maching ID to hwo object active_pins dictionary.
        self.input_A.set_machine(state_machine)
        self.input_B.set_machine(state_machine)

    def value(self):
        # Return the state of input A.
        return self.input_A.value()

    def off(self): # Turn off all outputs.
        self.SOL.off()
        self.LED.off()

# ----------------------------------------------------------------------------------------
# Hardware collections.
# ----------------------------------------------------------------------------------------

class Box():

    def __init__(self):

        # Instantiate components.
        self.left_poke   = Poke(port = 1, rising = 'left_poke', falling = 'left_poke_out')
        self.center_poke = Poke(port = 2, rising = 'high_poke', rising_B = 'low_poke')
        self.right_poke  = Poke(port = 3, rising = 'right_poke', falling = 'right_poke_out', rising_B = 'session_startstop')
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
