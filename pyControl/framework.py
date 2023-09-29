import pyb
import ujson
from . import timer
from . import state_machine as sm
from . import hardware as hw
from . import utility as ut

VERSION = "2.0rc1"


class pyControlError(BaseException):  # Exception for pyControl errors.
    pass


# Constants used to indicate event types, corresponding event tuple indicated in comment.

event_typ = b"E"  # External event   : (time, event_typ, [i]nput/[t]imer/[s]ync/[p]ublish/[u]ser/[a]pi, event_ID)
state_typ = b"S"  # State transition : (time, state_typ, state_ID)
print_typ = b"P"  # User print       : (time, print_typ, print_string)
hardw_typ = b"H"  # Harware callback : (time, hardw_typ, hardware_ID)
varbl_typ = b"V"  # Variable change  : (time, varbl_typ, [g]et/user_[s]et/[a]pi_set/[p]rint/s[t]art/[e]nd, json_str)
warng_typ = b"!"  # Warning          : (time, warng_typ, print_string)
stopf_typ = b"X"  # Stop framework   : (time, stopf_type)

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
    time, event_type, subtype, content = event
    timestamp = time.to_bytes(4, "little")
    if event_type == stopf_typ:  # Framework stop.
        usb_serial.send(b"\x07" + event_type + timestamp)
    else:
        data_bytes = (subtype + str(content)).encode()
        data_len = len(data_bytes).to_bytes(2, "little")
        checksum = (sum(data_len + timestamp + data_bytes)).to_bytes(2, "little")
        usb_serial.send(b"\x07" + event_type + data_len + timestamp + checksum + data_bytes)


def receive_data():
    # Read and process data from computer.
    global running
    new_byte = usb_serial.read(1)
    if new_byte == b"\x03":  # Serial command to stop run.
        running = False
    elif new_byte == b"V":  # Get/set variables command.
        data_len = int.from_bytes(usb_serial.read(2), "little")
        data = usb_serial.read(data_len)
        checksum = int.from_bytes(usb_serial.read(2), "little")
        if checksum != (sum(data) & 0xFFFF):
            return  # Bad checksum.
        data_str = data.decode()
        if data_str[0] in ("s", "a"):  # Set variable.
            v_name, v_value = eval(data_str[1:])
            if sm.set_variable(v_name, v_value):
                data_output_queue.put((current_time, varbl_typ, data_str[0], ujson.dumps({v_name: v_value})))
        elif data_str[0] == "g":  # Get variable.
            v_name = data_str[1:]
            v_value = sm.get_variable(v_name)
            data_output_queue.put((current_time, varbl_typ, "g", ujson.dumps({v_name: v_value})))
    elif new_byte in (b"E", b"P"):  # Publish event command.
        data_len = int.from_bytes(usb_serial.read(2), "little")
        data = usb_serial.read(data_len)
        data_str = data.decode()
        subtype = data_str[0]
        content = data_str[1:]
        checksum = int.from_bytes(usb_serial.read(2), "little")
        if checksum != (sum(data) & 0xFFFF):
            return  # Bad checksum.
        if new_byte == b"E":
            event_queue.put((current_time, event_typ, subtype, sm.events[content]))
        else:
            event_queue.put((current_time, print_typ, subtype, content))


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
            sm.process_event(event[3])
        # Priority 3: Check for elapsed timers.
        elif check_timers:
            timer.check()
        # Priority 4: Process timer event.
        elif timer.elapsed:
            event = timer.get()
            event_type, event_content = event[1], event[3]
            if event_type == event_typ:
                data_output_queue.put(event)
                sm.process_event(event_content)
            elif event_type == hardw_typ:
                hw.IO_dict[event_content]._timer_callback()
            elif event_type == state_typ:
                sm.goto_state(event_content)
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
    data_output_queue.put((current_time, stopf_typ, "", ""))
    usb_serial.setinterrupt(3)  # Enable 'ctrl+c' on serial raising KeyboardInterrupt.
    clock.deinit()
    hw.run_stop()
    sm.stop()
    while data_output_queue.available:
        output_data(data_output_queue.get())
