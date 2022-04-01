import pyb
from array import array
from . import framework as fw
from .utility import randint

# Ring buffer -----------------------------------------------------------------

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

# Variables -------------------------------------------------------------------

next_ID = 0 # Next hardware object ID.

IO_dict = {} # Dictionary {ID: IO_object} containing all hardware inputs and outputs.

available_timers = [2,3,4,5,7,8,9,10,11,12,13,14] # Hardware timers not in use. Used timers; 1: Framework clock tick, 6: DAC timed write.

default_pull = {'down': [], # Used when Mainboards are initialised to specify 
                'up'  : []} # default pullup or pulldown resistors for pins.

initialised = False # Set to True once hardware has been intiialised.

interrupt_queue = Ring_buffer()   # Queue for processing hardware interrupts.

stream_data_queue = Ring_buffer() # Queue for streaming data to computer.

# Functions -------------------------------------------------------------------

def assign_ID(hardware_object):
    # Assign unique ID to hardware object and put in IO_dict.
    global next_ID
    hardware_object.ID = next_ID
    IO_dict[hardware_object.ID] = hardware_object
    next_ID += 1

def initialise():
    # Called once after state machines setup and before framework first run.
    global initialised
    for IO_object in IO_dict.values():
        IO_object._initialise()
    initialised = True   

def run_start():
    # Called at start of each framework run.
    interrupt_queue.reset()
    stream_data_queue.reset()
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

def get_analog_inputs():
    # Print dict of analog inputs {name: {'ID': ID, 'Fs':sampling rate}}
    print({io.name:{'ID': io.ID, 'Fs': io.sampling_rate}
          for io in IO_dict.values() if hasattr(io, 'recording') and hasattr(io, 'sampling_rate')})

# IO_object -------------------------------------------------------------------

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

# Digital Input ---------------------------------------------------------------

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
        self.use_both_edges = False
        if self.rising_event_ID or self.falling_event_ID: # Setup interrupts.
            if self.debounce or (self.rising_event_ID and self.falling_event_ID):
                self.ExtInt(self.pin, pyb.ExtInt.IRQ_RISING_FALLING, self.pull, self._ISR)
                self.use_both_edges = True
            else:
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
        interrupt_queue.put(self.ID)

    def _process_interrupt(self):
        # Put apropriate event for interrupt in event queue.
        self._publish_if_edge_has_event(self.interrupt_timestamp)
        if self.debounce: # Set timer to deactivate debounce in self.debounce milliseconds.
            fw.timer.set(self.debounce, fw.hardw_typ, self.ID)

    def _timer_callback(self):
        # Called when debounce timer elapses, deactivates debounce and 
        # if necessary publishes event for edge missed during debounce.
        if not self.pin_state == self.pin.value(): # An edge has been missed.  
            self.pin_state = not self.pin_state  
            self._publish_if_edge_has_event(fw.current_time)
        self.debounce_active = False

    def _publish_if_edge_has_event(self, timestamp):
        # Publish event if detected edge has event ID assigned.
        if self.pin_state and self.rising_event_ID:          # Rising edge.
            fw.event_queue.put((timestamp, fw.event_typ, self.rising_event_ID))
        elif (not self.pin_state) and self.falling_event_ID: # Falling edge.
            fw.event_queue.put((timestamp, fw.event_typ, self.falling_event_ID))

    def value(self):
        # Return state of the input. 
        return self.pin.value()

    def _run_start(self): # Reset state of input, called at beginning of run.
        self.debounce_active = False      # Set True when pin is ignoring inputs due to debounce.
        if self.use_both_edges:
            self.pin_state = self.pin.value()
        self.interrupt_timestamp = 0
        self.decimate_counter = -1

# Analog data ----------------------------------------------------------------

class Data_channel(IO_object):
    # Data_channel can stream data continously to computer. This class can be subclassed or instantiated to stream
    # any kind of data back to the computer. the `Analog_input` class is an example of instantiating this class and adding functionality (event generation)
    # Serial data format for sending data to computer: '\x07A c i r l t k D' where:
    # \x07A Message start byte and A character indicating start of analog data chunk (2 bytes)
    # c data array typecode (1 byte)
    # i ID of analog input  (2 byte)
    # r sampling rate (Hz) (2 bytes)
    # l length of data array in bytes (2 bytes)
    # t timestamp of chunk start (ms)(4 bytes)
    # k checksum (2 bytes)
    # D data array bytes (variable)

    def __init__(self, name, sampling_rate, data_type='l'):
        assert data_type in ('b','B','h','H','l','L'), 'Invalid data_type.'
        assert not any([name == io.name for io in IO_dict.values() 
                        if isinstance(io, Data_channel)]), 'Analog inputs must have unique names.'
        self.name = name
        assign_ID(self)
        self.recording = False # Whether data is being sent to computer.
        self.sampling_rate = sampling_rate
        self.data_type = data_type
        self.bytes_per_sample = {'b':1,'B':1,'h':2,'H':2,'l':4,'L':4}[data_type]
        self.buffer_size = max(4, min(256 // self.bytes_per_sample, sampling_rate//10))
        self.buffers = (array(data_type, [0]*self.buffer_size), array(data_type, [0]*self.buffer_size))
        self.buffers_mv = (memoryview(self.buffers[0]), memoryview(self.buffers[1]))
        self.buffer_start_times = array('i', [0,0])
        self.data_header = array('B', b'\x07A' + data_type.encode() + 
            self.ID.to_bytes(2,'little') + sampling_rate.to_bytes(2,'little') + b'\x00'*8)
        self.write_buffer = 0 # Buffer to write new data to.
        self.write_index  = 0 # Buffer index to write new data to. 

    def record(self):
        # Start streaming data to computer.
        if not self.recording:
            self.write_index = 0  # Buffer index to write new data to. 
            self.buffer_start_times[self.write_buffer] = fw.current_time
            self.recording = True

    def stop(self):
        # Stop streaming data to computer.
        if self.recording:
            if self.write_index != 0:
                self._send_buffer(self.write_buffer, self.write_index)
            self.recording = False

    def put(self, sample: int):
        # load the buffer.
        self.buffers[self.write_buffer][self.write_index] = sample
        if self.recording:
            self.write_index = (self.write_index + 1) % self.buffer_size
            if self.write_index == 0: # Buffer full, switch buffers.
                self.write_buffer = 1 - self.write_buffer
                self.buffer_start_times[self.write_buffer] = fw.current_time
                stream_data_queue.put(self.ID)

    def _process_streaming(self):
        # Stream full buffer to computer.
        self._send_buffer(1-self.write_buffer)

    def _send_buffer(self, buffer_n, n_samples=False):
        # Send specified buffer to host computer.
        n_bytes = self.bytes_per_sample*n_samples if n_samples else self.bytes_per_sample*self.buffer_size
        self.data_header[7:9]  = n_bytes.to_bytes(2,'little')
        self.data_header[9:13] = self.buffer_start_times[buffer_n].to_bytes(4,'little')
        checksum = sum(self.buffers_mv[buffer_n][:n_samples] if n_samples else self.buffers[buffer_n])
        checksum += sum(self.data_header[2:13])
        self.data_header[13:15] = checksum.to_bytes(2,'little')
        fw.usb_serial.write(self.data_header)
        if n_samples: # Send first n_samples from buffer.
            fw.usb_serial.send(self.buffers_mv[buffer_n][:n_samples])
        else: # Send entire buffer.
            fw.usb_serial.send(self.buffers[buffer_n])

class Analog_input(IO_object):
    # Analog_input samples analog voltage from specified pin at specified frequency and uses `Data_channel`
    # to stream data continously to computer as well as generate framework events when 
    # voltage goes above / below specified value. The Analog_input class is subclassed
    # by other hardware devices that generate continous data such as the Rotory_encoder.

    def __init__(self, pin, name, sampling_rate, threshold=None, rising_event=None, 
                 falling_event=None, data_type='H'):
        if rising_event or falling_event:
            assert type(threshold) == int, 'Integer threshold must be specified if rising or falling events are defined.'
        assert not any([name == io.name for io in IO_dict.values() 
                if isinstance(io, Analog_input)]), 'Analog inputs must have unique names.'
        if pin: # pin argument can be None when Analog_input subclassed.
            self.ADC = pyb.ADC(pin)
            self.read_sample = self.ADC.read
        self.name = name
        assign_ID(self)
        # Data acqisition variables
        self.timer = pyb.Timer(available_timers.pop())
        self.acquiring = False # Whether input is being monitored.
        # Event generation variables
        self.threshold = threshold
        self.rising_event = rising_event
        self.falling_event = falling_event
        self.timestamp = 0
        self.crossing_direction = False
        # Data streaming
        self.data_channel = Data_channel(name, sampling_rate, data_type)


    def _initialise(self):
        # Set event codes for rising and falling events.
        self.rising_event_ID  = fw.events[self.rising_event ] if self.rising_event  in fw.events else False
        self.falling_event_ID = fw.events[self.falling_event] if self.falling_event in fw.events else False
        self.threshold_active = self.rising_event_ID or self.falling_event_ID

    def _run_start(self):
        if self.threshold_active: 
            self._start_acquisition()

    def _run_stop(self):
        self.data_channel.stop()
        if self.acquiring:
            self._stop_acquisition()

    def _start_acquisition(self):
        # Start sampling analog input values.
        self.timer.init(freq=self.data_channel.sampling_rate)
        self.timer.callback(self._timer_ISR)
        if self.threshold_active:
            self.above_threshold = self.read_sample() > self.threshold
        self.acquiring = True

    def record(self):
        # Start streaming data to computer.
        self.data_channel.record()
        if not self.acquiring: self._start_acquisition()

    def stop(self):
        # Stop streaming data to computer.
        self.data_channel.stop()
        if not self.threshold_active: 
            self._stop_acquisition()

    def _stop_acquisition(self):
        # Stop sampling analog input values.
        self.timer.deinit()
        self.acquiring = False

    def _timer_ISR(self, t):
        # Read a sample to the buffer, update write index.
        self.data_channel.put(self.read_sample())

        if self.threshold_active:
            new_above_threshold = self.buffers[self.write_buffer][self.write_index] > self.threshold
            if new_above_threshold != self.above_threshold: # Threshold crossing.
                self.above_threshold = new_above_threshold
                if ((    self.above_threshold and self.rising_event_ID) or 
                    (not self.above_threshold and self.falling_event_ID)):
                        self.timestamp = fw.current_time
                        self.crossing_direction = self.above_threshold
                        interrupt_queue.put(self.ID)

    def _process_interrupt(self):
        # Put event generated by threshold crossing in event queue.
        if self.crossing_direction:
            fw.event_queue.put((self.timestamp, fw.event_typ, self.rising_event_ID))
        else:
            fw.event_queue.put((self.timestamp, fw.event_typ, self.falling_event_ID))

# Digital Output --------------------------------------------------------------

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
        assign_ID(self)
        if pulse_enabled:
            self.enable_pulse()

    def on(self):
        self.pin.value(not self.inverted)
        self.state = True

    def off(self):
        if self.timer:
            self.timer.deinit()
        self.pin.value(self.inverted)
        self.state = False

    def toggle(self):
        if self.state:
            self.pin.value(self.inverted)
        else:
            self.pin.value(not self.inverted)
        self.state = not self.state  

    def enable_pulse(self): # Setup a hardware timer to allow pulsed output  
        self.timer = pyb.Timer(available_timers.pop())
        self.freq_multipliers = {10:10, 25:4, 50:2, 75:4}
        self.off_inds = {10:1, 25:1, 50:1, 75:3}

    def pulse(self, freq, duty_cycle=50, n_pulses=False): # Turn on pulsed output with specified frequency and duty cycle.
        assert duty_cycle in (10,25,50,75), 'duty_cycle must be 10, 25, 50 or 75'
        self.off_ind = self.off_inds[duty_cycle]
        self.i = 0
        self.fm = self.freq_multipliers[duty_cycle]
        self.n_pulses = n_pulses
        if self.n_pulses:
            self.pulse_n = 0
        self.on()
        self.timer.init(freq=freq*self.fm)
        self.timer.callback(self._ISR)

    def _ISR(self, t):
        self.i = (self.i + 1) % self.fm
        if self.i == 0:
            if self.n_pulses:
                self.pulse_n += 1
                if self.pulse_n == self.n_pulses:
                    self.off()
                    return
            self.toggle()

        elif self.i == self.off_ind:
            self.toggle()

# Port ------------------------------------------------------------------------

class Port():
    # Class representing one RJ45 behavioural hardware port.
    def __init__(self, DIO_A, DIO_B, POW_A, POW_B, DIO_C=None, POW_C=None, 
                 DAC=None, I2C=None, UART=None):
        self.DIO_A = DIO_A
        self.DIO_B = DIO_B
        self.DIO_C = DIO_C
        self.POW_A = POW_A
        self.POW_B = POW_B
        self.POW_C = POW_C
        self.DAC   = DAC
        self.I2C   = I2C
        self.UART  = UART

# Mainboard -------------------------------------------------------------------

class Mainboard():
    # Parent class for devboard and breakout boards.
    
    def set_pull_updown(self, pull): # Set default pullup/pulldown resistors.
        default_pull.update(pull)

# IO_expander_pin -------------------------------------------------------------

class IO_expander_pin():
    # Parent class for IO expander pins.
    pass

# Rsync -----------------------------------------------------------------------

class Rsync(IO_object):
    # Class for generating sync pulses with random inter-pulse interval.

    def __init__(self, pin, event_name='rsync', mean_IPI=5000, pulse_dur=50):
        assert 0.1*mean_IPI > pulse_dur, '0.1*mean_IPI must be greater than pulse_dur'
        self.sync_pin = pyb.Pin(pin, pyb.Pin.OUT)
        self.event_name = event_name
        self.pulse_dur = pulse_dur       # Sync pulse duration (ms)
        self.min_IPI = int(0.1*mean_IPI) 
        self.max_IPI = int(1.9*mean_IPI)
        assign_ID(self)

    def _initialise(self):
        self.event_ID  = fw.events[self.event_name] if self.event_name in fw.events else False

    def _run_start(self): 
        if self.event_ID:
            self.state = False # Whether output is high or low.
            self._timer_callback()

    def _run_stop(self):
        self.sync_pin.value(False)

    def _timer_callback(self):
        if self.state: # Pin high -> low, set timer for next pulse.
            fw.timer.set(randint(self.min_IPI, self.max_IPI), fw.hardw_typ, self.ID)
        else: # Pin low -> high, set timer for pulse duration.
            fw.timer.set(self.pulse_dur, fw.hardw_typ, self.ID)
            fw.data_output_queue.put((fw.current_time, fw.event_typ, self.event_ID))
        self.state = not self.state
        self.sync_pin.value(self.state)