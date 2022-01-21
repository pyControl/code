from array import array
import pyb
from . import hardware as hw

class pyControlError(BaseException): # Exception for pyControl errors.
    pass

# Constants used to indicate event types, corresponding event tuple indicated in comment.

event_typ = const(1) # External event   : (time, event_typ, event_ID) 
state_typ = const(2) # State transition : (time, state_typ, state_ID) 
timer_typ = const(3) # User timer       : (time, timer_typ, event_ID) 
print_typ = const(4) # User print       : (time, print_typ, print_string)
hardw_typ = const(5) # Harware callback : (time, hardw_typ, hardware_ID)
stopf_typ = const(6) # Stop framework   : (time, stopf_typ, None)
varbl_typ = const(7) # Variable change  : (time, varbl_typ, (v_name, v_str))

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

# Timer -----------------------------------------------------------------------

class Timer():

    def __init__(self):
        self.reset()

    def reset(self):
        self.active_timers = [] # list of event tuples: (trigger_time, event_type, data)
        self.paused_timers = [] # list of event tuples: (trigger_time, event_type, data)
        self.available = False
    
    def set(self, interval, event_type, event_data):
        # Set a timer to trigger specified event after 'interval' ms has elapsed.
        global current_time
        self.active_timers.append((current_time+int(interval), event_type, event_data))
        self.active_timers.sort(reverse=True)

    def check(self):
        #Check whether timers have triggered.
        global current_time, check_timers
        self.available = bool(self.active_timers) and (self.active_timers[-1][0] <= current_time)
        check_timers = False

    def get(self):
        # Get first timer event.
        global current_time
        event_tuple = self.active_timers.pop()
        self.available = bool(self.active_timers) and (self.active_timers[-1][0] <= current_time)
        return event_tuple

    def disarm(self, event_ID):
        # Remove all user timers with specified event_ID.
        self.active_timers = [t for t in self.active_timers 
                              if not (t[2] == event_ID and (t[1] in (event_typ, timer_typ)))]
        self.paused_timers = [t for t in self.paused_timers if not t[2] == event_ID]

    def pause(self, event_ID):
        # Pause all user timers with specified event_ID.
        global current_time
        self.paused_timers += [(t[0]-current_time,t[1], t[2]) for t in self.active_timers 
                               if (t[2] == event_ID and (t[1] in (event_typ, timer_typ)))]
        self.active_timers = [t for t in self.active_timers 
                              if not (t[2] == event_ID and (t[1] in (event_typ, timer_typ)))]

    def unpause(self, event_ID):
        # Unpause user timers with specified event.
        global current_time
        self.active_timers += [(t[0]+current_time,t[1], t[2]) for t in self.paused_timers if t[2] == event_ID]
        self.paused_timers = [t for t in self.paused_timers if not t[2] == event_ID]
        self.active_timers.sort(reverse=True)

    def remaining(self,event_ID):
        # Return time until timer for specified event elapses, returns 0 if no timer set for event.
        global current_time
        try:
            return next(t[0]-current_time for t in reversed(self.active_timers) 
                        if (t[1] == event_typ and t[2] == event_ID))
        except StopIteration:
            return 0

    def disarm_type(self, event_type):
        # Disarm all active timers of a particular type.
        self.active_timers = [t for t in self.active_timers if not t[1] == event_type]

# Framework variables and objects ---------------------------------------------

state_machine = None  # State machine object.

timer = Timer()  # Instantiate timer_array object.

event_queue = Event_queue() # Instantiate event que object.

data_output_queue = Event_queue() # Queue used for outputing events to serial line.

data_output = True  # Whether to output data to the serial line.

current_time = None # Time since run started (milliseconds).

running = False     # Set to True when framework is running, set to False to stop run.

usb_serial = pyb.USB_VCP()  # USB serial port object.

states = {} # Dictionary of {state_name: state_ID}

events = {} # Dictionary of {event_name: event_ID}

ID2name = {} # Dictionary of {ID: state_or_event_name}

clock = pyb.Timer(1) # Timer which generates clock tick.

check_timers = False # Flag to say timers need to be checked, set True by clock tick.

start_time = 0 # Time at which framework run is started.

# Framework functions ---------------------------------------------------------

def _clock_tick(timer):
    # Set flag to check timers, called by hardware timer once each millisecond.
    global check_timers, current_time, start_time
    current_time = pyb.elapsed_millis(start_time)
    check_timers = True

def register_machine(sm):
    global state_machine, states, events, ID2name
    # Adds state machine states and events to framework states and events dicts,
    # if IDs are provided, checks these are valid, otherwise asign IDs.
    assert (type(sm.smd.states) in (dict, list) and (type(sm.smd.states) == type(sm.smd.events))), \
        'States and events must both be lists or both be dicts'

    if type(sm.smd.states) == list: # Assign IDs
        states = {s: i+1 for s, i in zip(sm.smd.states, range(len(sm.smd.states)))}
        events = {e: i+1+len(sm.smd.states)
                  for e, i in zip(sm.smd.events, range(len(sm.smd.events)))}
        sm.smd.states = states 
        sm.smd.events = events

    else: # Check IDs are valid.
        IDs = list(sm.smd.states.values()) + list(sm.smd.events.values())
        assert all([type(i) == int and i > 0 for i in IDs]) and len(set(IDs)) == len(IDs), \
            'Event and state IDs must be unique positive integers.'

    ID2name = {ID: name for name, ID in list(states.items()) + list(events.items())}
    state_machine = sm

def get_events():
    # Print events as dict.
    print(events)

def get_states():
    # Print states as a dict.
    print(states)

def get_variables():
    # Print state machines variables as dict {v_name: repr(v_value)}
    print({k: repr(v) for k, v in state_machine.variables.__dict__.items()})

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
            if state_machine._set_variable(v_name, v_str):
                data_output_queue.put((current_time, varbl_typ, (v_name, v_str)))
        elif data[-1:] == b'g': # Get variable.
            v_name = data[:-1].decode()
            v_str = state_machine._get_variable(v_name)
            data_output_queue.put((current_time, varbl_typ, (v_name, v_str)))

def run(duration=None):
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
    state_machine._start()
    if duration: # Set timer to stop framework.
        timer.set(duration*1000, (stopf_typ, None))
    # Run
    while running:
        # Priority 1: Process hardware interrupts.
        if hw.interrupt_queue.available: 
            hw.IO_dict[hw.interrupt_queue.get()]._process_interrupt()
        # Priority 2: Process event from queue.
        elif event_queue.available: 
            event = event_queue.get()
            data_output_queue.put(event)
            state_machine._process_event(ID2name[event[2]])
        # Priority 3: Check for elapsed timers.
        elif check_timers:
            timer.check()
        # Priority 4: Process timer event.
        elif timer.available: 
            event = timer.get()
            if  event[1] == timer_typ:
                state_machine._process_event(ID2name[event[2]])
            elif event[1] == event_typ:
                data_output_queue.put(event)
                state_machine._process_event(ID2name[event[2]])
            elif event[1] == hardw_typ:
                hw.IO_dict[event[2]]._timer_callback()
            elif event[1] == state_typ:
                state_machine.goto_state(ID2name[event[2]])
            elif event[1] == stopf_typ:
                running = False
        # Priority 5: Check for serial input from computer.
        elif usb_serial.any(): 
            recieve_data()
        # Priority 6: Stream analog data.
        elif hw.stream_data_queue.available: 
            hw.IO_dict[hw.stream_data_queue.get()]._process_streaming()
        # Priority 7: Output framework data.
        elif data_output_queue.available: 
            output_data(data_output_queue.get())
    # Post run
    usb_serial.setinterrupt(3) # Enable 'ctrl+c' on serial raising KeyboardInterrupt.
    clock.deinit()
    hw.run_stop()
    state_machine._stop()
    while data_output_queue.available:
        output_data(data_output_queue.get())