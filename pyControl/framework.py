from array import array
import pyb
from . import hardware as hw

# Constants used to indicate special event types:

timer_evt    = const(-1) # Timer generated event.
debounce_evt = const(-2) # Digital_input debounce timer event.
goto_evt     = const(-3) # timed_goto_state event.
print_evt    = const(-4) # User print event.
data_evt     = const(-5) # User data output event.
stop_fw_evt  = const(-6) # Stop framework event.

# The Event_queue and Timer classes store events for future processing
# as lists of tuples.  The following event tuple types are in use:

# (event_ID, timestamp) # External event, ID is positive integer.
# (state_ID, timestamp) # State transition, ID is a positive integer.
# (event_ID, timer_evt) # Timer generated event, ID is a positive integer.
# (print_evt, timestamp, 'print_string') # User print event.
# (data_evt, timestamp, name, typecode, data_array) # User data output event.
# (goto_evt, State_machine_ID)     # timed_goto_state event.
# (debounce_evt, Digital_input_ID) # Digital_input debouce timer.
# (stop_fw_evt, None)   # Stop framework event.

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
    
    def set(self, interval, event):
        # Set a timer to trigger specified event after 'interval' ms has elapsed.
        global current_time
        self.active_timers.append((current_time+interval, event))
        self.active_timers.sort(reverse = True)

    def check(self):
        #Check whether any timers have triggered, place events in event que.
        global current_time, start_time, check_timers
        while self.active_timers and self.active_timers[-1][0] <= current_time:
            event_queue.put(self.active_timers.pop()[1])
        check_timers = False

    def disarm(self, event):
        # Remove all active timers with specified event.
        self.active_timers = [t for t in self.active_timers if not t[1] == event]

# ----------------------------------------------------------------------------------------
# Framework variables and objects
# ----------------------------------------------------------------------------------------

state_machines = []  # List to hold state machines.

timer = Timer()  # Instantiate timer_array object.

event_queue = Event_queue() # Instantiate event que object.

data_output_queue = Event_queue() # Queue used for outputing events to serial line.

data_output = True  # Whether to output data to the serial line.

verbose = False     # True: output names, False: output IDs

current_time = None # Time since run started (milliseconds).

running = False     # Set to True when framework is running, set to False to stop run.

usb_serial = pyb.USB_VCP()  # USB serial port object.

states = {} # Dictionary of {state_name: state_ID}

events = {} # Dictionary of {event_name: event_ID}

ID2name = {} # Dictionary of {ID: state_or_event_name}

clock = pyb.Timer(4) # Timer which generates clock tick.

check_timers = False # Flag to say timers need to be checked, set True by clock tick.

interrupts_waiting = False # Flag to say external interrupt waiting to be processed.

start_time = 0 # Time at which framework run is started.

# ----------------------------------------------------------------------------------------
# Framework functions.
# ----------------------------------------------------------------------------------------

def _clock_tick(timer):
    # Set flag to check timers, called by hardware timer once each millisecond.
    global check_timers, current_time, start_time
    current_time = pyb.millis() - start_time
    check_timers = True

def register_machine(state_machine):
    # Adds state machine states and events to framework states and events dicts,
    # if IDs are provided, checks these are valid, otherwise asigns valid ID automatically.
    # No two state machines can have states with the same name.  Two state machines can
    # share the same event, but the event must have the same ID if ID is specified.

    next_ID = 1

    def assign_IDs(name_list):
        # Assign lowest available positive integer IDs to list of state or event names.
        name_dict = {}
        for name in name_list:
            if name in events.keys(): # Events shared by multiple state machines have same ID.
                name_dict[name] = events[name]
            else:
                while next_ID in ID2name.keys():
                    next_ID += 1
                name_dict[name] = next_ID
                next_ID += 1
        return name_dict

    if type(state_machine.smd.states) == list:
        state_machine.smd.states = assign_IDs(state_machine.smd.states)

    if type(state_machine.smd.events) == list:
        state_machine.smd.events = assign_IDs(state_machine.smd.events)

    for state_name, ID in state_machine.smd.states.items():
        assert state_name not in states.keys(), '! State names cannot be repeated.'
        assert type(ID) == int and ID > 0,      '! State and event IDs must be positive integers.'
        assert ID not in ID2name.keys(),        '! Different states or events cannot have same ID'

    for event_name, ID in state_machine.smd.events.items():
        if event_name in events.keys():
            assert ID == events[event_name], '! Events with same name must have same ID. ' 
        else:
            assert ID not in ID2name.keys(), '! Different states or events cannot have same ID'
        assert type(ID) == int and ID > 0,   '! State and event IDs must be positive integers.'

    states.update(state_machine.smd.states)
    events.update(state_machine.smd.events)
    ID2name.update({ID:name for name, ID in list(state_machine.smd.states.items()) +
                                            list(state_machine.smd.events.items())})
    state_machine.ID = len(state_machines)
    state_machines.append(state_machine)

def print_events():
    """ Print  events as a dictionary"""
    print("E {}".format(events))

def print_states():
    """ Print states as a dictionary"""
    print("S {}".format(states))

def output_data(event):
    # Output data to serial line.
    if event[0] > 0:  # Print event or state change.
        if verbose: # Print event/state name.
            print('D {} {}'.format(event[1], ID2name[event[0]]))
        else: # Print event/state ID.
            print('D {} {}'.format(event[1], event[0]))   
    elif event[0] == print_evt: # Print user generated output string.
        print('P {} {}'.format(event[1], event[2]))
    elif event[0] == data_evt: # Output user generated data.
        data_bytes = bytes(event[4])
        usb_serial.send('B {} {} \a{}'.format(event[1], event[2], event[3]).encode()
                        + len(data_bytes).to_bytes(2, 'little') + data_bytes + b'\n')         

def _update():
    # Perform framework update functions in order of priority.
    global current_time, interrupts_waiting, running
    if interrupts_waiting: # Priority 1: Process hardware interrupts.
        interrupts_waiting = False
        for digital_input in hw.active_inputs:
            if digital_input.interrupt_triggered:
                digital_input._process_interrupt()
    elif check_timers: # Priority 2: Check for elapsed timers.
        timer.check() 
    elif event_queue.available(): # Priority 3: Process event from queue.
        event = event_queue.get()   
        if event[0] > 0: # State machine event.
            if event[1] != timer_evt and data_output: # External event -> place in output queue.
                data_output_queue.put(event)
            for state_machine in state_machines:
                state_machine._process_event(ID2name[event[0]])
        elif event[0] == debounce_evt:
            hw.active_inputs[event[1]]._deactivate_debounce()
        elif event[0] == goto_evt:
            state_machines[event[1]]._process_timed_goto_state()
        elif event[0] == stop_fw_evt:
            running = False
    elif usb_serial.any(): # Priority 4: Check for serial input from computer.
        bytes_recieved = usb_serial.read()
        if bytes_recieved == b'E':      # Serial command to stop run.
            running = False
    elif data_output_queue.available(): # Priority 5: Output data.
        output_data(data_output_queue.get())

def run(duration = None):
    # Run framework for specified number of seconds.
    # Pre run----------------------------
    global current_time, start_time, running
    timer.reset()
    event_queue.reset()
    data_output_queue.reset()
    if not hw.initialised: hw.initialise()
    hw.reset()
    current_time = 0
    start_time = pyb.millis()
    clock.init(freq=1000)
    clock.callback(_clock_tick)
    # Run--------------------------------
    running = True
    for state_machine in state_machines:
        state_machine._start()
    if duration: # Set timer to stop framework.
        timer.set(duration*1000, (stop_fw_evt, None))
    while running:
        _update()
    # Post run---------------------------
    clock.deinit()
    for state_machine in state_machines:
        state_machine._stop()  
    while data_output_queue.available():
        output_data(data_output_queue.get())

def get_current_time():
    # Get the current framework time.
    global current_time
    return current_time