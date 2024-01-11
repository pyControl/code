import pyb
from array import array
from . import timer
from . import framework as fw
from . import state_machine as sm
from .utility import randint, warning

# Ring buffer -----------------------------------------------------------------


class Ring_buffer:
    #  Ring buffer for storing data from interrupt service routines.
    def __init__(self, buffer_length=20):
        self.buffer_length = buffer_length
        self.buffer = array("i", [0] * self.buffer_length)
        self.reset()

    def reset(self):
        # Empty buffer.
        self.read_ind = 0
        self.write_ind = 0
        self.available = False

    @micropython.native
    def put(self, x: int):
        # Put value in buffer.
        self.buffer[self.write_ind] = x
        self.write_ind = (self.write_ind + 1) % self.buffer_length
        self.available = True

    @micropython.native
    def get(self) -> int:
        # Get value from buffer
        x = self.buffer[self.read_ind]
        self.read_ind = (self.read_ind + 1) % self.buffer_length
        self.available = self.read_ind != self.write_ind
        return x


# Variables -------------------------------------------------------------------

next_ID = 0  # Next hardware object ID.

IO_dict = {}  # Dictionary {ID: IO_object} containing all hardware inputs and outputs.

available_timers = [3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14]  # Hardware timers not in use
# Used timers; 1: Framework clock tick, 2: Audio write_timed, 6: DAC write_timed.

initialised = False  # Set to True once hardware has been intiialised.

interrupt_queue = Ring_buffer()  # Queue for processing hardware interrupts.

stream_data_queue = Ring_buffer()  # Queue for streaming data to computer.

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
    # Print dict of analog input info.
    print(
        {
            ai.ID: {"name": ai.name, "fs": ai.sampling_rate, "dtype": ai.data_type, "plot": ai.plot}
            for ai in IO_dict.values()
            if isinstance(ai, Analog_channel)
        }
    )


# IO_object -------------------------------------------------------------------


class IO_object:
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
    def __init__(self, pin, rising_event=None, falling_event=None, debounce=5, pull=None):
        # Digital_input class provides functionallity to generate framework events when a
        # specified pin on the Micropython board changes state. Seperate events can be
        # specified for rising and falling edges.
        # By defalt debouncing is used to prevent multiple events being triggered very
        # close together in time if the edges are not clean.  The debouncing method used
        # ensures that transient inputs shorter than the debounce duration still generate
        # rising and faling edges.  Debouncing incurs some overheads so should be turned
        # off for inputs with clean edges and high event rates.
        # Arguments:
        # pin           - micropython pin to use
        # rising_event  - Name of event triggered on rising edges.
        # falling_event - Name of event triggered on falling edges.
        # debounce      - Minimum time interval between events (ms),
        #                 set to False to deactive debouncing.
        # pull          - used to enable internal pullup or pulldown resitors.
        if pull is None:
            pull = pyb.Pin.PULL_NONE
        elif pull == "up":
            pull = pyb.Pin.PULL_UP
        elif pull == "down":
            pull = pyb.Pin.PULL_DOWN
        self.pull = pull
        if isinstance(pin, IO_expander_pin):  # Pin is on an IO expander.
            self.pin = pin
            self.ExtInt = pin.IOx.ExtInt
            self.expander_pin = True
        else:  # Pin is pyboard pin.
            self.pin = pyb.Pin(pin, pyb.Pin.IN, pull=pull)
            self.ExtInt = pyb.ExtInt
            self.expander_pin = False
        self.rising_event = rising_event
        self.falling_event = falling_event
        self.debounce = debounce

        assign_ID(self)

    def _initialise(self):
        # Set event codes for rising and falling events, configure interrupts.
        self.rising_event_ID = sm.events[self.rising_event] if self.rising_event in sm.events else False
        self.falling_event_ID = sm.events[self.falling_event] if self.falling_event in sm.events else False
        self.use_both_edges = False
        if self.rising_event_ID or self.falling_event_ID:  # Setup interrupts.
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
            return  # Ignore interrupt as too soon after previous interrupt.
        self.interrupt_timestamp = fw.current_time
        if self.debounce:  # Digital input uses debouncing.
            self.debounce_active = True
            self.pin_state = not self.pin_state
        elif self.use_both_edges:
            self.pin_state = self.pin.value()
        if self.expander_pin:  # _ISR() called from main loop.
            self._process_interrupt()
        else:  # _ISR() called by interrupt.
            interrupt_queue.put(self.ID)

    def _process_interrupt(self):
        # Put apropriate event for interrupt in event queue.
        self._publish_if_edge_has_event(self.interrupt_timestamp)
        if self.debounce:  # Set timer to deactivate debounce in self.debounce milliseconds.
            timer.set(self.debounce, fw.HARDW_TYP, "", self.ID)

    def _timer_callback(self):
        # Called when debounce timer elapses, deactivates debounce and
        # if necessary publishes event for edge missed during debounce.
        if not self.pin_state == self.pin.value():  # An edge has been missed.
            self.pin_state = not self.pin_state
            self._publish_if_edge_has_event(fw.current_time)
        self.debounce_active = False

    def _publish_if_edge_has_event(self, timestamp):
        # Publish event if detected edge has event ID assigned.
        if self.pin_state and self.rising_event_ID:  # Rising edge.
            fw.event_queue.put(fw.Datatuple(timestamp, fw.EVENT_TYP, "i", self.rising_event_ID))
        elif (not self.pin_state) and self.falling_event_ID:  # Falling edge.
            fw.event_queue.put(fw.Datatuple(timestamp, fw.EVENT_TYP, "i", self.falling_event_ID))

    def value(self):
        # Return state of the input.
        return self.pin.value()

    def _run_start(self):  # Reset state of input, called at beginning of run.
        self.debounce_active = False  # Set True when pin is ignoring inputs due to debounce.
        if self.use_both_edges:
            self.pin_state = self.pin.value()
        self.interrupt_timestamp = 0


# Analog data ----------------------------------------------------------------


class Analog_input(IO_object):
    # Analog_input samples analog voltage from specified pin at specified frequency and
    # streams data to computer. Optionally can generate framework events when voltage
    #  goes above / below specified value theshold.

    def __init__(self, pin, name, sampling_rate, threshold=None, rising_event=None, falling_event=None, data_type="H"):
        if rising_event or falling_event:
            self.threshold = Analog_threshold(threshold, rising_event, falling_event)
        else:
            self.threshold = False
        self.timer = pyb.Timer(available_timers.pop())
        if pin:  # pin argument can be None when Analog_input subclassed.
            self.ADC = pyb.ADC(pin)
            self.read_sample = self.ADC.read
        self.name = name
        self.Analog_channel = Analog_channel(name, sampling_rate, data_type)
        assign_ID(self)

    def _run_start(self):
        # Start sampling timer, initialise threshold, aquire first sample.
        self.timer.init(freq=self.Analog_channel.sampling_rate)
        self.timer.callback(self._timer_ISR)
        if self.threshold:
            self.threshold.run_start(self.read_sample())
        self._timer_ISR(0)

    def _run_stop(self):
        self.timer.deinit()

    @micropython.native
    def _timer_ISR(self, t):
        # Read a sample to the buffer, update write index.
        sample = self.read_sample()
        self.Analog_channel.put(sample)
        if self.threshold:
            self.threshold.check(sample)

    def record(self):  # For backward compatibility.
        pass

    def stop(self):  # For backward compatibility
        pass


class Analog_channel(IO_object):
    # Buffers analog data and streams it to computer in chunks.
    # Data format is 13 byte header + data array:
    #     \x07 Message start byte (1 bytes)
    #     message checksum (2 bytes)
    #     message length (2 bytes)
    #     timestamp of chunk start (ms) (4 bytes)
    #     message type [A] and subtype [_] (2 byte)
    #     ID of analog input (2 byte)
    #     data array bytes (variable)

    def __init__(self, name, sampling_rate, data_type, plot=True):
        assert data_type in ("b", "B", "h", "H", "i", "I"), "Invalid data_type."
        assert not any(
            [name == io.name for io in IO_dict.values() if isinstance(io, Analog_channel)]
        ), "Analog signals must have unique names."
        self.name = name
        assign_ID(self)
        self.sampling_rate = sampling_rate
        self.data_type = data_type
        self.plot = plot
        self.bytes_per_sample = {"b": 1, "B": 1, "h": 2, "H": 2, "i": 4, "I": 4}[data_type]
        self.buffer_size = max(4, min(256 // self.bytes_per_sample, sampling_rate // 10))
        self.buffers = (array(data_type, [0] * self.buffer_size), array(data_type, [0] * self.buffer_size))
        self.buffers_mv = (memoryview(self.buffers[0]), memoryview(self.buffers[1]))
        self.buffer_start_times = array("i", [0, 0])
        self.data_header = array("B", b"\x07" + b"_" * 8 + b"A_" + self.ID.to_bytes(2, "little"))
        self.write_buffer = 0  # Buffer to write new data to.
        self.write_index = 0  # Buffer index to write new data to.

    def _run_start(self):
        self.write_index = 0  # Buffer index to write new data to.

    def _run_stop(self):
        if self.write_index != 0:
            self.send_buffer(run_stop=True)

    @micropython.native
    def put(self, sample: int):
        # Put a sample in the buffer.
        if self.write_index == 0:  # Record buffer start timestamp.
            self.buffer_start_times[self.write_buffer] = fw.current_time
        self.buffers[self.write_buffer][self.write_index] = sample
        self.write_index = (self.write_index + 1) % self.buffer_size
        if self.write_index == 0:  # Buffer full, switch buffers.
            self.write_buffer = 1 - self.write_buffer
            stream_data_queue.put(self.ID)

    @micropython.native
    def send_buffer(self, run_stop=False):
        # Send buffer to host computer.
        if run_stop:  # Send the contents of the current write buffer.
            buffer_n = self.write_buffer
            n_samples = self.write_index
        else:  # Send the buffer not currently being written to.
            buffer_n = 1 - self.write_buffer
            n_samples = self.buffer_size
        message_len = 8 + self.bytes_per_sample * n_samples
        self.data_header[3:5] = message_len.to_bytes(2, "little")
        self.data_header[5:9] = self.buffer_start_times[buffer_n].to_bytes(4, "little")
        checksum = sum(self.data_header[5:])
        checksum += sum(self.buffers_mv[buffer_n][:n_samples] if run_stop else self.buffers[buffer_n])
        self.data_header[1:3] = checksum.to_bytes(2, "little")
        fw.usb_serial.write(self.data_header)
        if run_stop:
            fw.usb_serial.send(self.buffers_mv[buffer_n][:n_samples])
        else:
            fw.usb_serial.send(self.buffers[buffer_n])


class Analog_threshold(IO_object):
    # Generates framework events when an analog signal goes above or below specified threshold.

    def __init__(self, threshold=None, rising_event=None, falling_event=None):
        assert isinstance(
            threshold, int
        ), "Integer threshold must be specified if rising or falling events are defined."
        self.threshold = threshold
        self.rising_event = rising_event
        self.falling_event = falling_event
        self.timestamp = 0
        self.crossing_direction = False
        assign_ID(self)

    def _initialise(self):
        # Set event codes for rising and falling events.
        self.rising_event_ID = sm.events[self.rising_event] if self.rising_event in sm.events else False
        self.falling_event_ID = sm.events[self.falling_event] if self.falling_event in sm.events else False
        self.threshold_active = self.rising_event_ID or self.falling_event_ID

    def run_start(self, sample):
        self.above_threshold = sample > self.threshold

    def _process_interrupt(self):
        # Put event generated by threshold crossing in event queue.
        if self.crossing_direction:
            fw.event_queue.put(fw.Datatuple(self.timestamp, fw.EVENT_TYP, "i", self.rising_event_ID))
        else:
            fw.event_queue.put(fw.Datatuple(self.timestamp, fw.EVENT_TYP, "i", self.falling_event_ID))

    @micropython.native
    def check(self, sample):
        new_above_threshold = sample > self.threshold
        if new_above_threshold != self.above_threshold:  # Threshold crossing.
            self.above_threshold = new_above_threshold
            if (self.above_threshold and self.rising_event_ID) or (not self.above_threshold and self.falling_event_ID):
                self.timestamp = fw.current_time
                self.crossing_direction = self.above_threshold
                interrupt_queue.put(self.ID)


# Digital Output --------------------------------------------------------------


class Digital_output(IO_object):
    def __init__(self, pin, inverted=False):
        if isinstance(pin, IO_expander_pin):
            pin.set_mode(pyb.Pin.OUT)
            self.pin = pin  # Pin is on an IO expander.
        else:
            self.pin = pyb.Pin(pin, pyb.Pin.OUT)  # Pin is pyboard pin.
        self.inverted = inverted  # Set True for inverted output.
        self.timer = False  # Replaced by timer object if pulsed output is used.
        self.off()
        assign_ID(self)

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

    def pulse(self, freq, duty_cycle=50, n_pulses=False, load_warning=True):
        # Turn on pulsed output with specified frequency and duty cycle.
        assert duty_cycle % 5 == 0, "duty cycle must be a multiple of 5 between 5 and 95%"
        if not self.timer:
            self.timer = pyb.Timer(available_timers.pop())
        self.fm = int(100 / next(x for x in (50, 25, 20, 10, 5) if duty_cycle % x == 0))
        self.off_ind = int(duty_cycle / 100 * self.fm)
        self.i = 0
        self.n_pulses = n_pulses
        if self.n_pulses:
            self.pulse_n = 0
        int_freq = freq * self.fm
        if load_warning and int_freq > 2000:
            warning("This pulse freq and duty_cycle will use > 10% of pyboard processor resources.")
        self.timer.init(freq=int_freq)
        self.timer.callback(self._ISR)
        self.on()

    @micropython.native
    def _ISR(self, t):
        self.i += 1
        if self.i == self.off_ind:
            if self.n_pulses:
                self.pulse_n += 1
                if self.pulse_n == self.n_pulses:
                    self.off()
                    return
            self.toggle()
        elif self.i == self.fm:
            self.i = 0
            self.toggle()


# Port ------------------------------------------------------------------------


class Port:
    # Class representing one RJ45 behavioural hardware port.
    def __init__(self, DIO_A, DIO_B, POW_A, POW_B, DIO_C=None, POW_C=None, DAC=None, I2C=None, UART=None):
        self.DIO_A = DIO_A
        self.DIO_B = DIO_B
        self.DIO_C = DIO_C
        self.POW_A = POW_A
        self.POW_B = POW_B
        self.POW_C = POW_C
        self.DAC = DAC
        self.I2C = I2C
        self.UART = UART


# IO_expander_pin -------------------------------------------------------------


class IO_expander_pin:
    # Parent class for IO expander pins.
    pass


# Rsync -----------------------------------------------------------------------


class Rsync(IO_object):
    # Class for generating sync pulses with random inter-pulse interval.

    def __init__(self, pin, event_name="rsync", mean_IPI=5000, pulse_dur=50):
        assert 0.1 * mean_IPI > pulse_dur, "0.1*mean_IPI must be greater than pulse_dur"
        self.sync_pin = pyb.Pin(pin, pyb.Pin.OUT)
        self.event_name = event_name
        self.pulse_dur = pulse_dur  # Sync pulse duration (ms)
        self.min_IPI = int(0.1 * mean_IPI)
        self.max_IPI = int(1.9 * mean_IPI)
        assign_ID(self)

    def _initialise(self):
        self.event_ID = sm.events[self.event_name] if self.event_name in sm.events else False

    def _run_start(self):
        if self.event_ID:
            self.state = False  # Whether output is high or low.
            self._timer_callback()

    def _run_stop(self):
        self.sync_pin.value(False)

    def _timer_callback(self):
        if self.state:  # Pin high -> low, set timer for next pulse.
            timer.set(randint(self.min_IPI, self.max_IPI), fw.HARDW_TYP, "", self.ID)
        else:  # Pin low -> high, set timer for pulse duration.
            timer.set(self.pulse_dur, fw.HARDW_TYP, "", self.ID)
            fw.data_output_queue.put(fw.Datatuple(fw.current_time, fw.EVENT_TYP, "s", self.event_ID))
        self.state = not self.state
        self.sync_pin.value(self.state)
