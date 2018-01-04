import pyb
from array import array
from . import framework as fw

# ----------------------------------------------------------------------------------------
# Ring buffer
# ----------------------------------------------------------------------------------------

class Ring_buffer():
    #  Ring buffer for storing data from interrupt service routines.
    def __init__(self, buffer_length=20):
        self.buffer_length = buffer_length
        self.buffer = array('i', [0] * self.buffer_length)
        self.reset()

    def reset(self):
        # Empty buffer.
        self.read_ind  = 0
        self.write_ind = 0
        self.available = False
        self.full = False

    @micropython.native
    def put(self, x: int):
        # Put value in buffer.
        if self.full:
            print('! Ring buffer full')
            return
        self.buffer[self.write_ind] = x
        self.write_ind = (self.write_ind + 1) % self.buffer_length
        self.available = True
        self.full = self.read_ind == self.write_ind

    @micropython.native
    def get(self) -> int:
        # Get value from buffer
        if self.available:
            x = self.buffer[self.read_ind]
            self.read_ind = (self.read_ind + 1) % self.buffer_length
            self.available = self.read_ind != self.write_ind
            self.full = False
            return x

# ----------------------------------------------------------------------------------------
# Variables.
# ----------------------------------------------------------------------------------------

ID_generator = (i for i in range(1<<16)) # Generator for hardware object IDs.

IO_dict = {} # Dictionary {ID: IO_object} containing all hardware inputs and outputs.

available_timers = [7,8,9,10,11,12,13,14] # Hardware timers not in use by other fuctions.

default_pull = {'down': [], # Used when Mainboards are initialised to specify 
                'up'  : []} # default pullup or pulldown resistors for pins.

initialised = False # Set to True once hardware has been intiialised.

high_priority_queue = Ring_buffer() # Hardware objects that need to be processed as soon as possible.

low_priority_queue  = Ring_buffer() # Hardware objects that need to be processed at some point.

# ----------------------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------------------

def assign_ID(hardware_object):
    # Assign unique ID to hardware object and put in IO_dict.
    hardware_object.ID = next(ID_generator)
    IO_dict[hardware_object.ID] = hardware_object

def initialise():
    # Called once after state machines setup and before framework first run.
    global initialised
    for IO_object in IO_dict.values():
        IO_object._initialise()
    initialised = True   

def run_start():
    # Called at start of each framework run.
    high_priority_queue.reset()
    low_priority_queue.reset()
    for IO_object in IO_dict.values():
        IO_object._run_start()

def run_stop():
    # Called at end of each framework run.
    for IO_object in IO_dict.values():
        IO_object._run_stop()
    off()

def off():
    # Turn off hardware objects.
    for IO_object in IO_dict.values():
        IO_object.off()

def print_analog_inputs():
    # Print dictionary of Analog_inputs {IDs:names}.
    print('A {}'.format({io.ID: io.name for io in IO_dict.values() if isinstance(io, Analog_input)}))


# ----------------------------------------------------------------------------------------
# IO_object
# ----------------------------------------------------------------------------------------

class IO_object():
    # Parent class for all pyControl input and output objects.

    def _initialise(self):
        pass

    def _run_start(self):
        pass

    def _run_stop(self):
        pass

    def off(self):
        pass

# ----------------------------------------------------------------------------------------
# Digital Input
# ----------------------------------------------------------------------------------------

class Digital_input(IO_object):
    def __init__(self, pin, rising_event=None, falling_event=None, debounce=5, decimate=False, pull=None):
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
        if isinstance(pin, IO_expander_pin): # Pin is on an IO expander.
            self.pin = pin
            self.ExtInt = pin.IOx.ExtInt
        else:                                # Pin is pyboard pin.
            self.pin = pyb.Pin(pin, pyb.Pin.IN, pull=pull)
            self.ExtInt = pyb.ExtInt
        self.rising_event = rising_event
        self.falling_event = falling_event
        self.debounce = debounce     
        self.decimate = decimate
        assign_ID(self)

    def _initialise(self):
        # Set event codes for rising and falling events, configure interrupts.
        self.rising_event_ID  = fw.events[self.rising_event ] if self.rising_event  in fw.events else False
        self.falling_event_ID = fw.events[self.falling_event] if self.falling_event in fw.events else False
        if self.rising_event_ID or self.falling_event_ID: # Setup interrupts.
            if self.debounce or (self.rising_event_ID and self.falling_event_ID):
                self.ExtInt(self.pin, pyb.ExtInt.IRQ_RISING_FALLING, self.pull, self._ISR)
                self.use_both_edges = True
            else:
                self.use_both_edges = False
                if self.rising_event_ID:
                    self.ExtInt(self.pin, pyb.ExtInt.IRQ_RISING, self.pull, self._ISR)
                    self.pin_state = True
                else:
                    self.ExtInt(self.pin, pyb.ExtInt.IRQ_FALLING, self.pull, self._ISR)
                    self.pin_state = False

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
        high_priority_queue.put(self.ID)

    def _process(self, priority):
        # Put apropriate event for interrupt in event queue.
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

    def _run_start(self): # Reset state of input, called at beginning of run.
        self.debounce_active = False      # Set True when pin is ignoring inputs due to debounce.
        if self.use_both_edges:
            self.pin_state = self.pin.value()
        self.interrupt_timestamp = 0
        self.decimate_counter = -1

# ----------------------------------------------------------------------------------------
# Analog input.
# ----------------------------------------------------------------------------------------

class Analog_input(IO_object):
    # Analog_input samples analog voltage from specified pin at specified frequency and can
    # stream data to continously to computer as well as generate framework events when 
    # voltage goes above / below specified value.
    # Serial data format for streaming: '\a c i r l t D' where:
    # a\ ASCII bell character indicating start of analog data chunk (1 byte)
    # c data array typecode (1 byte)
    # i ID of analog input  (2 byte)
    # r sampling rate (Hz) (2 bytes)
    # l length of data array in bytes (2 bytes)
    # t timestamp of chunk start (ms)(4 bytes)
    # D data array bytes (variable)

    def __init__(self, pin, name, sampling_rate, threshold=None, rising_event=None, falling_event=None):
        if rising_event or falling_event:
            assert type(threshold) == int, 'Integer threshold must be specified if rising or falling events are defined.'
        self.name = name
        self.sampling_rate = sampling_rate
        self.threshold = threshold
        self.rising_event = rising_event
        self.falling_event = falling_event
        self.timestamp = 0
        self.buffer_size = 128
        self.buffers = (array('H', [0]*self.buffer_size),array('H', [0]*self.buffer_size))
        self.buffer_start_times = array('i', [0,0])
        self.timer = pyb.Timer(available_timers.pop()) 
        self.ADC = pyb.ADC(pin)
        self.recording = False # Whether data is being sent to computer.
        self.acquiring = False # Whether input is being monitored.
        assign_ID(self)
        self.data_header = (b'\aH' + self.ID.to_bytes(2,'little') + 
                            self.sampling_rate.to_bytes(2,'little') +
                            (2*self.buffer_size).to_bytes(2,'little'))

    def _initialise(self):
        # Set event codes for rising and falling events.
        self.rising_event_ID  = fw.events[self.rising_event ] if self.rising_event  in fw.events else False
        self.falling_event_ID = fw.events[self.falling_event] if self.falling_event in fw.events else False
        self.threshold_active = self.rising_event_ID or self.falling_event_ID

    def _run_start(self):
        self.write_buffer = 0 # Buffer to write new data to.
        self.write_index  = 0 # Buffer index to write new data to. 
        if self.threshold_active: 
            self._start_acquisition()

    def _run_stop(self):
        if self.acquiring:
            self._stop_acquisition()

    def _start_acquisition(self):
        # Start sampling analog input values.
        self.timer.init(freq=self.sampling_rate)
        self.timer.callback(self._timer_ISR)
        if self.threshold_active:
            self.above_threshold = self.ADC.read() > self.threshold
        self.acquiring = True

    def record(self):
        # Start streaming data to computer.
        self.write_index = 0  # Buffer index to write new data to. 
        self.buffer_start_times[self.write_buffer] = fw.current_time
        self.recording = True
        if not self.acquiring: self._start_acquisition()

    def stop(self):
        # Stop streaming data to computer.
        self.recording = False
        if not self.threshold_active: 
            self._stop_acquisition()

    def _stop_acquisition(self):
        # Stop sampling analog input values.
        self.timer.deinit()
        self.recording = False
        self.acquiring = False

    def _timer_ISR(self, t):
        # Read a sample to the buffer, update write index.
        self.buffers[self.write_buffer][self.write_index] = self.ADC.read()
        if self.threshold_active:
            new_above_threshold = self.buffers[self.write_buffer][self.write_index] > self.threshold
            if new_above_threshold != self.above_threshold: # Threshold crossing.
                self.above_threshold = new_above_threshold
                if ((    self.above_threshold and self.rising_event_ID) or 
                    (not self.above_threshold and self.falling_event_ID)):
                        self.timestamp = fw.current_time
                        self.crossing_direction = self.above_threshold
                        high_priority_queue.put(self.ID)
        if self.recording:
            self.write_index = (self.write_index + 1) % self.buffer_size
            if self.write_index == 0: # Buffer full, switch buffers.
                self.write_buffer = 1 - self.write_buffer
                self.buffer_start_times[self.write_buffer] = fw.current_time
                low_priority_queue.put(self.ID)

    def _process(self, priority):
        if priority: # Process threshold crossing.
            if self.crossing_direction:
                fw.event_queue.put((self.rising_event_ID, self.timestamp))
            else:
                fw.event_queue.put((self.falling_event_ID, self.timestamp))
        else: # Send full buffer to computer.
            fw.usb_serial.write(self.data_header)
            fw.usb_serial.write(self.buffer_start_times[1- self.write_buffer].to_bytes(4,'little'))
            fw.usb_serial.send(self.buffers[1- self.write_buffer])

# ----------------------------------------------------------------------------------------
# Digital Output.
# ----------------------------------------------------------------------------------------

class Digital_output(IO_object):

    def __init__(self, pin, inverted=False, pulse_enabled=False):
        if isinstance(pin, IO_expander_pin):
            pin.set_mode(pyb.Pin.OUT)
            self.pin = pin # Pin is on an IO expander.
        else:
            self.pin = pyb.Pin(pin, pyb.Pin.OUT)  # Pin is pyboard pin.
        self.inverted = inverted # Set True for inverted output.
        self.timer = False # Replaced by timer object if pulse enabled.
        self.off()
        if pulse_enabled:
            self.enable_pulse()
        all_outputs.append(self)

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

# ----------------------------------------------------------------------------------------
# IO_expander_pin
# ----------------------------------------------------------------------------------------

class IO_expander_pin():
    # Parent class for IO expander pins.
    pass