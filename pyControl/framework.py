from array import array
import pyb
from . import hardware as hw

# Constants used to indicate special event types:

timer_evt    = const(-1) # Timer generated event.
debounce_evt = const(-2) # Digital_input debounce timer event.
goto_evt     = const(-3) # timed_goto_state event.
print_evt    = const(-4) # User print event.
stop_fw_evt  = const(-5) # Stop framework event.
varset_evt  = const(-6) # Variable changed event.

# The Event_queue and Timer classes store events for future processing
# as lists of tuples.  The following event tuple types are in use:

# (event_ID, timestamp) # External event, ID is positive integer.
# (state_ID, timestamp) # State transition, ID is a positive integer.
# (event_ID, timer_evt) # Timer generated event, ID is a positive integer.
# (print_evt, timestamp, 'data_bytes') # User print event.
# (goto_evt)     # timed_goto_state event.
# (debounce_evt, Digital_input_ID) # Digital_input debouce timer.
# (stop_fw_evt, None)   # Stop framework event.
# (varset_evt, timestamp, v_name, v_str) # Variable changed.

class pyControlError(BaseException):
    pass

# ----------------------------------------------------------------------------------------
# Event_queue
# ----------------------------------------------------------------------------------------

class Event_queue():  
    # First-in first-out event queue.
    def __init__(self):
        self.reset()

    def reset(self):
        # Empty queue.
        self.Q = []

    def put(self, event):
        # Put event in queue.  
        self.Q.append(event)

    def get(self):
        # Get event from queue
        return(self.Q.pop(0))

    def available(self):
        # Return True if queue contains events.
        return len(self.Q) > 0

# ----------------------------------------------------------------------------------------
# Timer
# ----------------------------------------------------------------------------------------

class Timer():

    def __init__(self):
        self.reset()

    def reset(self):
        self.active_timers = [] # list of tuples: (trigger_time, event)
        self.paused_timers = [] # list of tuples: (remaining_time, event)
    
    def set(self, interval, event):
        # Set a timer to trigger specified event after 'interval' ms has elapsed.
        global current_time
        self.active_timers.append((current_time+interval, event))
        self.active_timers.sort(reverse=True)

    def check(self):
        #Check whether any timers have triggered, place events in event que.
        global current_time, start_time, check_timers
        while self.active_timers and self.active_timers[-1][0] <= current_time:
            event_queue.put(self.active_timers.pop()[1])
        check_timers = False

    def disarm(self, event):
        # Remove all active timers with specified event.
        self.active_timers = [t for t in self.active_timers if not t[1] == event]
        self.paused_timers = [t for t in self.paused_timers if not t[1] == event]

    def pause(self, event):
        # Pause all timers with specified event.
        global current_time
        self.paused_timers += [(t[0]-current_time,t[1]) for t in self.active_timers if t[1] == event]
        self.active_timers = [t for t in self.active_timers if not t[1] == event]

    def unpause(self, event):
        # Unpause timers with specified event.
        global current_time
        self.active_timers += [(t[0]+current_time,t[1]) for t in self.paused_timers if t[1] == event]
        self.paused_timers = [t for t in self.paused_timers if not t[1] == event]
        self.active_timers.sort(reverse=True)

    def remaining(self,event):
        # Return time until timer for specified event elapses, returns 0 if no timer set for event.
        global current_time
        try:
            return next(t[0]-current_time for t in reversed(self.active_timers) if t[1] == event)
        except StopIteration:
            return 0

# ----------------------------------------------------------------------------------------
# Framework variables and objects
# ----------------------------------------------------------------------------------------

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

# ----------------------------------------------------------------------------------------
# Framework functions.
# ----------------------------------------------------------------------------------------

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
    # Print first instantiated state machines variables as dict {v_name: repr(v_value)}
    print({k: repr(v) for k, v in state_machine.smd.v.__dict__.items()})

def output_data(event):
    # Output data to computer.
    if event[0] > 0:  # send event or state change.
        timestamp = event[1].to_bytes(4, 'little') 
        ID        = event[0].to_bytes(2, 'little')
        checksum  = sum(timestamp + ID).to_bytes(2, 'little') 
        usb_serial.send(b'D' + timestamp + ID + checksum)
    elif event[0] in (print_evt, varset_evt): # send user generated output string.
        if event[0] == print_evt: # send user generated output string.
            start_byte = b'P'
            data_bytes = event[2].encode()
        elif event[0] == varset_evt: # Variable changed.
            start_byte = b'V'
            data_bytes = event[2].encode() + b' ' + event[3].encode()
        data_len = len(data_bytes).to_bytes(2, 'little')  
        timestamp = event[1].to_bytes(4, 'little')
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
                data_output_queue.put((varset_evt, current_time, v_name, v_str))
        elif data[-1:] == b'g': # Get variable.
            v_name = data[:-1].decode()
            v_str = str(state_machine._get_variable(v_name))
            data_output_queue.put((varset_evt, current_time, v_name, v_str))

def _update():
    # Perform framework update functions in order of priority.
    global running

    if hw.high_priority_queue.available: # Priority 1: Process high priority hardware.
        hw.IO_dict[hw.high_priority_queue.get()]._process(priority=True)

    elif check_timers: # Priority 2: Check for elapsed timers.
        timer.check() 

    elif event_queue.available(): # Priority 3: Process event from queue.
        event = event_queue.get()   
        if event[0] > 0: # State machine event.
            if event[1] != timer_evt and data_output: # External event -> place in output queue.
                data_output_queue.put(event)
            state_machine._process_event(ID2name[event[0]])
        elif event[0] == debounce_evt:
            hw.IO_dict[event[1]]._deactivate_debounce()
        elif event[0] == goto_evt:
            state_machine._process_timed_goto_state()
        elif event[0] == stop_fw_evt:
            running = False
    elif usb_serial.any(): # Priority 4: Check for serial input from computer.
        recieve_data()

    elif hw.low_priority_queue.available: # Priority 5: Process low priority hardware.
        hw.IO_dict[hw.low_priority_queue.get()]._process(priority=False)

    elif data_output_queue.available(): # Priority 6: Output data.
        output_data(data_output_queue.get())

def run(duration = None):
    # Run framework for specified number of seconds.
    # Pre run
    global current_time, start_time, running
    timer.reset()
    event_queue.reset()
    data_output_queue.reset()
    if not hw.initialised: hw.initialise()
    hw.run_start()
    current_time = 0
    start_time = pyb.millis()
    clock.init(freq=1000)
    clock.callback(_clock_tick)
    usb_serial.setinterrupt(-1) # Disable 'ctrl+c' on serial raising KeyboardInterrupt.
    running = True
    state_machine._start()
    if duration: # Set timer to stop framework.
        timer.set(duration*1000, (stop_fw_evt, None))
    # Run
    while running:
        _update()
    # Post run
    usb_serial.setinterrupt(3) # Enable 'ctrl+c' on serial raising KeyboardInterrupt.
    clock.deinit()
    hw.run_stop()
    state_machine._stop()
    while data_output_queue.available():
        output_data(data_output_queue.get())