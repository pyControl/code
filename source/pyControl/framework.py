import pyb
import ujson
from ucollections import namedtuple
from . import timer
from . import state_machine as sm
from . import hardware as hw
from . import utility as ut

VERSION = "2.0.2"


class pyControlError(BaseException):  # Exception for pyControl errors.
    pass


Datatuple = namedtuple("Datatuple", ["time", "type", "subtype", "content"])

# Constants used to indicate data types, corresponding data tuple indicated in comment.

EVENT_TYP = b"E"  # Event            : (time, EVENT_TYP, [i]nput/[t]imer/[s]ync/[p]ublish/[u]ser/[a]pi, event_ID)
STATE_TYP = b"S"  # State transition : (time, STATE_TYP, "", state_ID)
PRINT_TYP = b"P"  # User print       : (time, PRINT_TYP, "", print_string)
HARDW_TYP = b"H"  # Harware callback : (time, HARDW_TYP, "", hardware_ID)
VARBL_TYP = b"V"  # Variable change  : (time, VARBL_TYP, [g]et/user_[s]et/[a]pi_set/[p]rint/s[t]art/[e]nd, json_str)
WARNG_TYP = b"!"  # Warning          : (time, WARNG_TYP, "", print_string)
STOPF_TYP = b"X"  # Stop framework   : (time, STOPF_TYP, "", "")

# Event_queue -----------------------------------------------------------------


class Event_queue:
    # First-in first-out event queue.
    def __init__(self):
        self.reset()

    def reset(self):
        # Empty queue.
        self.Q = []
        self.available = False

    def put(self, event_tuple):
        # Put event in queue.
        self.Q.append(event_tuple)
        self.available = True

    def get(self):
        # Get event tuple from queue
        self.available = len(self.Q) > 1
        return self.Q.pop(0)


# Framework variables and objects ---------------------------------------------

event_queue = Event_queue()  # Instantiate event que object.

data_output_queue = Event_queue()  # Queue used for outputing events to serial line.

data_output = True  # Whether to output data to the serial line.

current_time = None  # Time since run started (milliseconds).

running = False  # Set to True when framework is running, set to False to stop run.

usb_serial = pyb.USB_VCP()  # USB serial port object.

clock = pyb.Timer(1)  # Timer which generates clock tick.

check_timers = False  # Flag to say timers need to be checked, set True by clock tick.

start_time = 0  # Time at which framework run is started.

# Framework functions ---------------------------------------------------------


def _clock_tick(t):
    # Set flag to check timers, called by hardware timer once each millisecond.
    global check_timers, current_time
    current_time = pyb.elapsed_millis(start_time)
    check_timers = True


def output_data(event):
    # Output data to computer.
    if not data_output:
        return
    timestamp = event.time.to_bytes(4, "little")
    subtype_byte = event.subtype.encode() if event.subtype else b"_"
    content_bytes = str(event.content).encode() if event.content else b""
    message = timestamp + event.type + subtype_byte + content_bytes
    message_len = len(message).to_bytes(2, "little")
    checksum = sum(message).to_bytes(2, "little")
    usb_serial.send(b"\x07" + checksum + message_len + message)


def receive_data():
    # Read and process data from computer.
    global running
    new_byte = usb_serial.read(1)
    if new_byte == b"\x03":  # Serial command to stop run.
        running = False
    elif new_byte in (VARBL_TYP, EVENT_TYP):
        data_len = int.from_bytes(usb_serial.read(2), "little")
        data_and_checksum = usb_serial.recv(data_len + 2, timeout=1)
        checksum = int.from_bytes(data_and_checksum[-2:], "little")
        if checksum != (sum(data_and_checksum[:-2]) & 0xFFFF):
            return  # Bad checksum, data was corrupted or recieve timedout.
        data_str = data_and_checksum[:-2].decode()
        if new_byte == VARBL_TYP:  # Get/set variables command.
            if data_str[0] in ("s", "a"):  # Set variable.
                v_name, v_value = eval(data_str[1:])
                if sm.set_variable(v_name, v_value):
                    data_output_queue.put(
                        Datatuple(current_time, VARBL_TYP, data_str[0], ujson.dumps({v_name: v_value}))
                    )
            elif data_str[0] == "g":  # Get variable.
                v_name = data_str[1:]
                v_value = sm.get_variable(v_name)
                data_output_queue.put(Datatuple(current_time, VARBL_TYP, "g", ujson.dumps({v_name: v_value})))
        elif new_byte == EVENT_TYP:  # Trigger event command.
            subtype = data_str[0]
            event_ID = int(data_str[1:])
            event_queue.put(Datatuple(current_time, EVENT_TYP, subtype, event_ID))


def run():
    # Run framework for specified number of seconds.
    # Pre run
    global current_time, start_time, running
    timer.reset()
    event_queue.reset()
    data_output_queue.reset()
    if not hw.initialised:
        hw.initialise()
    usb_serial.setinterrupt(-1)  # Disable 'ctrl+c' on serial raising KeyboardInterrupt.
    current_time = 0
    ut.print_variables(when="t")
    start_time = pyb.millis()
    clock.init(freq=1000)
    clock.callback(_clock_tick)
    sm.start()
    hw.run_start()
    running = True
    # Run
    while running:
        # Priority 1: Process hardware interrupts.
        if hw.interrupt_queue.available:
            hw.IO_dict[hw.interrupt_queue.get()]._process_interrupt()
        # Priority 2: Process event from queue.
        elif event_queue.available:
            event = event_queue.get()
            data_output_queue.put(event)
            sm.process_event(event.content)
        # Priority 3: Check for elapsed timers.
        elif check_timers:
            timer.check()
        # Priority 4: Process timer event.
        elif timer.elapsed:
            event = timer.get()
            if event.type == EVENT_TYP:
                if event.subtype:
                    data_output_queue.put(event)
                sm.process_event(event.content)
            elif event.type == HARDW_TYP:
                hw.IO_dict[event.content]._timer_callback()
            elif event.type == STATE_TYP:
                sm.goto_state(event.content)
        # Priority 5: Check for serial input from computer.
        elif usb_serial.any():
            receive_data()
        # Priority 6: Stream analog data.
        elif hw.stream_data_queue.available:
            hw.IO_dict[hw.stream_data_queue.get()].send_buffer()
        # Priority 7: Output framework data.
        elif data_output_queue.available:
            output_data(data_output_queue.get())
    # Post run
    ut.print_variables(when="e")
    data_output_queue.put(Datatuple(current_time, STOPF_TYP, "", ""))
    usb_serial.setinterrupt(3)  # Enable 'ctrl+c' on serial raising KeyboardInterrupt.
    clock.deinit()
    hw.run_stop()
    sm.stop()
    while data_output_queue.available:
        output_data(data_output_queue.get())
