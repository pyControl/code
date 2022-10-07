import pyb
from . import timer
from . import state_machine as sm
from . import hardware as hw

VERSION = '1.8'

class pyControlError(BaseException): # Exception for pyControl errors.
    pass

# Constants used to indicate event types, corresponding event tuple indicated in comment.

event_typ = const(1) # External event   : (time, event_typ, event_ID) 
state_typ = const(2) # State transition : (time, state_typ, state_ID) 
timer_typ = const(3) # User timer       : (time, timer_typ, event_ID) 
print_typ = const(4) # User print       : (time, print_typ, print_string)
hardw_typ = const(5) # Harware callback : (time, hardw_typ, hardware_ID)
varbl_typ = const(6) # Variable change  : (time, varbl_typ, (v_name, v_str))

# Event_queue -----------------------------------------------------------------

class Event_queue():  
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
        return(self.Q.pop(0))

# Framework variables and objects ---------------------------------------------

event_queue = Event_queue() # Instantiate event que object.

data_output_queue = Event_queue() # Queue used for outputing events to serial line.

data_output = True  # Whether to output data to the serial line.

current_time = None # Time since run started (milliseconds).

running = False     # Set to True when framework is running, set to False to stop run.

usb_serial = pyb.USB_VCP()  # USB serial port object.

clock = pyb.Timer(1) # Timer which generates clock tick.

check_timers = False # Flag to say timers need to be checked, set True by clock tick.

start_time = 0 # Time at which framework run is started.

# Framework functions ---------------------------------------------------------

def _clock_tick(t):
    # Set flag to check timers, called by hardware timer once each millisecond.
    global check_timers, current_time
    current_time = pyb.elapsed_millis(start_time)
    check_timers = True

def output_data(event):
    # Output data to computer.
    if event[1] in  (event_typ, state_typ): # send event or state change.
        timestamp = event[0].to_bytes(4, 'little') 
        ID        = event[2].to_bytes(2, 'little')
        checksum  = sum(timestamp + ID).to_bytes(2, 'little') 
        usb_serial.send(b'\x07D' + timestamp + ID + checksum)
    elif event[1] in (print_typ, varbl_typ): # send user generated output string.
        if event[1] == print_typ: # send user generated output string.
            start_byte = b'\x07P'
            data_bytes = event[2].encode()
        elif event[1] == varbl_typ: # Variable changed.
            start_byte = b'\x07V'
            data_bytes = event[2][0].encode() + b' ' + event[2][1].encode()
        data_len = len(data_bytes).to_bytes(2, 'little')  
        timestamp = event[0].to_bytes(4, 'little')
        checksum  = (sum(data_len + timestamp) + sum(data_bytes)).to_bytes(2, 'little')
        usb_serial.send(start_byte + data_len + timestamp + checksum + data_bytes)

def recieve_data():
    # Read and process data from computer.
    global running
    new_byte = usb_serial.read(1) 
    if new_byte == b'\x03': # Serial command to stop run.
        running = False
    elif new_byte == b'V': # Get/set variables command.
        data_len = int.from_bytes(usb_serial.read(2), 'little')
        data = usb_serial.read(data_len)
        checksum = int.from_bytes(usb_serial.read(2), 'little')
        if not checksum == (sum(data) & 0xFFFF):
            return  # Bad checksum.
        if data[-1:] == b's': # Set variable.
            v_name, v_str = eval(data[:-1])
            if sm.set_variable(v_name, v_str):
                data_output_queue.put((current_time, varbl_typ, (v_name, v_str)))
        elif data[-1:] == b'g': # Get variable.
            v_name = data[:-1].decode()
            v_str = sm.get_variable(v_name)
            data_output_queue.put((current_time, varbl_typ, (v_name, v_str)))

def run():
    # Run framework for specified number of seconds.
    # Pre run
    global current_time, start_time, running
    timer.reset()
    event_queue.reset()
    data_output_queue.reset()
    if not hw.initialised: hw.initialise()
    current_time = 0
    hw.run_start()
    start_time = pyb.millis()
    clock.init(freq=1000)
    clock.callback(_clock_tick)
    usb_serial.setinterrupt(-1) # Disable 'ctrl+c' on serial raising KeyboardInterrupt.
    running = True
    sm.start()
    # Run
    while running:
        # Priority 1: Process hardware interrupts.
        if hw.interrupt_queue.available: 
            hw.IO_dict[hw.interrupt_queue.get()]._process_interrupt()
        # Priority 2: Process event from queue.
        elif event_queue.available: 
            event = event_queue.get()
            data_output_queue.put(event)
            sm.process_event(event[2])
        # Priority 3: Check for elapsed timers.
        elif check_timers:
            timer.check()
        # Priority 4: Process timer event.
        elif timer.elapsed: 
            event = timer.get()
            if  event[1] == timer_typ:
                sm.process_event(event[2])
            elif event[1] == event_typ:
                data_output_queue.put(event)
                sm.process_event(event[2])
            elif event[1] == hardw_typ:
                hw.IO_dict[event[2]]._timer_callback()
            elif event[1] == state_typ:
                sm.goto_state(event[2])
        # Priority 5: Check for serial input from computer.
        elif usb_serial.any(): 
            recieve_data()
        # Priority 6: Stream analog data.
        elif hw.stream_data_queue.available: 
            hw.IO_dict[hw.stream_data_queue.get()].send_buffer()
        # Priority 7: Output framework data.
        elif data_output_queue.available: 
            output_data(data_output_queue.get())
    # Post run
    usb_serial.setinterrupt(3) # Enable 'ctrl+c' on serial raising KeyboardInterrupt.
    clock.deinit()
    hw.run_stop()
    sm.stop()
    while data_output_queue.available:
        output_data(data_output_queue.get())