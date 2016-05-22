from array import array
import pyb
from .utility import second
from . import hardware as hw

# ----------------------------------------------------------------------------------------
# Event Que
# ----------------------------------------------------------------------------------------

ID_null_value =  0  # Event ID null value, no event may have this ID.

class Event_queue():
    #  Queue for holding event tuples: (event_ID, timestamp)
    def __init__(self, buffer_length = 20):
        self.buffer_length = buffer_length
        self.reset()

    def reset(self):
        # Empty queue, set IDs to null value.
        self.ID_buffer = array('i', [ID_null_value] * self.buffer_length)
        self.TS_buffer = array('l', [0]  * self.buffer_length)
        self.read_index  = 0
        self.write_index = 0

    def put(self, event):
        # Put event in que.  
        assert self.ID_buffer[self.write_index] == ID_null_value, 'Event queue buffer full'
        self.ID_buffer[self.write_index] = event[0]
        self.TS_buffer[self.write_index] = event[1]  
        self.write_index = (self.write_index + 1) % self.buffer_length

    def get(self):
        # Get event from buffer.  If no events are available return None.
        event_ID   = self.ID_buffer[self.read_index]
        timestamp  = self.TS_buffer[self.read_index] 
        self.ID_buffer[self.read_index] = ID_null_value
        if event_ID != ID_null_value:
            self.read_index = (self.read_index + 1) % self.buffer_length
            return (event_ID, timestamp)
        else:
            return None

    def available(self):
        # Return True if buffer contains events.
        return self.ID_buffer[self.read_index] != ID_null_value

# ----------------------------------------------------------------------------------------
# Timer
# ----------------------------------------------------------------------------------------

class Timer_orig():
    # Timer which uses a list which expands and contracts as timers are set and elapse.

    def __init__(self):
        self.reset()

    def reset(self):
        self.active_timers = [] # list of tuples: (event_ID, trigger_time)

    def set(self, event_ID, interval):
        # Set a timer to trigger with specified event ID after 'interval' ms has elapsed.
        global current_time
        trigger_time = current_time + interval
        self.active_timers.append((event_ID, trigger_time))

    def check(self):
        #Check whether any timers have triggered and place corresponding events into 
        # event que.
        global current_time
        for i,active_timer in enumerate(self.active_timers):
            if current_time - active_timer[1] >= 0: # Timer has elapsed.
                if active_timer[0] <= 0: # Digital_input debounce timer.
                    # Event IDs <= 0 are used to index digital inputs for debounce timing.
                    hw.digital_inputs[-active_timer[0]]._deactivate_debounce() 
                else:
                    event_queue.put((active_timer[0], -1)) 
                    # Timestamp of -1 indictates not to put timer events in to output queue.
                self.active_timers.pop(i)

    def disarm(self,event_ID):
        # Remove all active timers with specified event ID.
        self.active_timers = [t for t in self.active_timers if not t[0] == event_ID]


class Timer_sorted():
    # Timer which uses a list which expands and contracts as timers are set and elapse.

    def __init__(self):
        self.reset()

    def reset(self):
        self.active_timers = [] # list of tuples: (event_ID, trigger_time)
    
    def set(self, event_ID, interval):
        # Set a timer to trigger with specified event ID after 'interval' ms has elapsed.
        global current_time
        self.active_timers.append((current_time + interval, event_ID))
        self.active_timers.sort(reverse = True)

    def check(self):
        #Check whether any timers have triggered, place events in event que.
        global current_time, check_timers
        while self.active_timers and self.active_timers[-1][0] < current_time:
            ID = self.active_timers.pop()[1]
            if ID <= 0: # IDs <= 0 are used to index digital inputs for debounce timing. 
                hw.digital_inputs[-ID]._deactivate_debounce() 
            else:
                event_queue.put((ID, -1)) # Timestamp-1 indictates not to put timer events in to output queue.
        check_timers = False

    def disarm(self,event_ID):
        # Remove all active timers with specified event ID.
        self.active_timers = [t for t in self.active_timers if not t[1] == event_ID]


class Timer_array():
    # Timer which uses a linked list structure so that checking should be O(1) but
    # setting is slower.

    def __init__(self, n_timers = 20):
        self.n_timers = n_timers
        self.reset()

    def reset(self):
        self.ID_array = array('i', [-1] * self.n_timers) # Event ID array.
        self.TT_array = array('i', [-1] * self.n_timers) # Trigger time array.
        self.NT_array = array('i', [-1] * self.n_timers) # Next timer index array.
        self.first_timer = -1 # Index of first timer to trigger.

    def set(self, event_ID, interval):
        # Set a timer to trigger with specified event ID after 'interval' ms has elapsed.
        global current_time
        i=0 # Index to store new timer.
        while not self.TT_array[i] == -1: # Find first empty slot.
            i+=1
            if i >= self.n_timers:
                print('Warning, timer array full.')
        trigger_time = current_time + interval 
        self.ID_array[i] = event_ID
        self.TT_array[i] = trigger_time
        # Update linked list.
        next_timer = self.first_timer
        prev_timer = -1
        timer_set = False
        while not timer_set:
            if self.TT_array[next_timer] == -1: # New timer is last timer.
                timer_set = True
                self.NT_array[i] = -1
            elif self.TT_array[next_timer] > trigger_time:
                timer_set = True
                self.NT_array[i] = next_timer
            if timer_set:
                if prev_timer == -1:
                    self.first_timer = i
                else:
                    self.NT_array[prev_timer] = i
            else:
                prev_timer = next_timer
                next_timer = self.NT_array[next_timer]

    def check(self):
        global current_time
        while ((not self.first_timer == -1) and 
               (current_time-self.TT_array[self.first_timer] >= 0)): # Timer has elapsed.
            if self.ID_array[self.first_timer] <= 0: # Digital_input debounce timer.
                # Event IDs <= 0 are used to index digital inputs for debounce timing.
                hw.digital_inputs[
                    -self.ID_array[self.first_timer]]._deactivate_debounce() 
            else:
                event_queue.put((self.ID_array[self.first_timer], -1)) 
                # Timestamp of -1 indictates not to put timer events in to output queue.
            self.TT_array[self.first_timer] = -1
            self.first_timer = self.NT_array[self.first_timer]

    def disarm(self,event_ID):
        # Remove all active timers with specified event ID.
        next_timer = self.first_timer
        prev_timer = -1
        while not next_timer == -1:
            if self.ID_array[next_timer] == event_ID:
                self.TT_array[next_timer] = -1
                if not prev_timer == -1:
                    self.NT_array[prev_timer] = self.NT_array[next_timer]
                prev_timer = next_timer
                next_timer = self.NT_array[next_timer]

# ----------------------------------------------------------------------------------------
# Framework variables and objects
# ----------------------------------------------------------------------------------------

state_machines = []  # List to hold state machines.

timer = Timer_sorted()  # Instantiate timer_array object.

event_queue = Event_queue() # Instantiate event que object.

interrupts_waiting = False # Set true if interrupt waiting to be processed.

data_output_queue = Event_queue() # Queue used for outputing events to serial line.

print_queue = [] # Queue for strings output using print function. 

data_output = True  # Whether to output data to the serial line.

verbose = False     # True: output names, False: output IDs

current_time = None # Time since run started (milliseconds).

running = False     # Set to True when framework is running, set to False to stop run.

start_time = 0      # Time when run was started.

usb_serial = pyb.USB_VCP()  # USB serial port object.

states = {} # Dictionary of {state_name: state_ID}

events = {} # Dictionary of {event_name: event_ID}

ID2name = {} # Dictionary of {ID: state_or_event_name}

clock = pyb.Timer(1)

check_timers = False # Flag to say timers need to be checked, set True by clock tick.

# ----------------------------------------------------------------------------------------
# Framework functions.
# ----------------------------------------------------------------------------------------

def _clock_tick(timer):
    global check_timers, current_time
    check_timers = True
    current_time += 1

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
        assert state_name not in states.keys(), 'State names cannot be repeated.'
        assert type(ID) == int and ID > 0,      'State and event IDs must be positive integers.'
        assert ID not in ID2name.keys(),        'Different states or events cannot have same ID'

    for event_name, ID in state_machine.smd.events.items():
        if event_name in events.keys():
            assert ID == events[event_name], 'Events with same name must have same ID. ' 
        else:
            assert ID not in ID2name.keys(), 'Different states or events cannot have same ID'
        assert type(ID) == int and ID > 0,   'State and event IDs must be positive integers.'

    states.update(state_machine.smd.states)
    events.update(state_machine.smd.events)
    ID2name.update({ID:name for name, ID in list(state_machine.smd.states.items()) +
                                            list(state_machine.smd.events.items())})

    state_machines.append(state_machine)

def print_IDs():
    # Print event and state IDs
    print('States:')
    for state_ID in sorted(states.values()):
        print(ID2name[state_ID] + ': ' + str(state_ID))
    print('Events:')
    for event_ID in sorted(events.values()):
        print(ID2name[event_ID]  + ': ' +  str(event_ID))

def output_data(event):
    # Output data to serial line.
    if event[0] == -1: # Print user generated output string.
        print_string = print_queue.pop(0)
        if type(print_string) != str:
            print_string = repr(print_string)
        print('{} '.format(event[1]) + print_string)
    else:  # Print event or state change.
        if verbose: # Print event/state name.
            event_name = ID2name[event[0]]
            print('{} '.format(event[1]) + event_name)
        else: # Print event/state ID.
            print('{} {}'.format(event[1], event[0]))

n_cycles = 0

def _update():
    # Perform framework update functions in order of priority.
    global current_time, interrupts_waiting, start_time, running, n_cycles
    #current_time = pyb.elapsed_millis(start_time)
    if check_timers:
        timer.check() 
    if interrupts_waiting:         # Priority 1: Process interrupts.
        interrupts_waiting = False
        for digital_input in hw.digital_inputs:
            if digital_input.interrupt_triggered:
                digital_input._process_interrupt()
    elif event_queue.available():  # Priority 2: Process events in queue.
        event = event_queue.get()       
        if event[1] >= 0 and data_output: # Not timer event -> place in output queue.
            data_output_queue.put(event)
        for state_machine in state_machines:
            state_machine._process_event(ID2name[event[0]])
    elif usb_serial.any():        # Priority 3: Check for serial input from computer.
        bytes_recieved = usb_serial.readall()
        if bytes_recieved == b'E': # Code to stop run over serial.
            running = False
    elif data_output_queue.available(): # Priority 4: Output data.
        output_data(data_output_queue.get())
    n_cycles += 1


def run(duration = None):
    # Run framework for specified number of seconds.
    # Pre run----------------------------
    global current_time, start_time, running, n_cycles
    timer.reset()
    event_queue.reset()
    data_output_queue.reset()
    if not hw.hardware_definition:
        hw.initialise()
    hw.reset()
    #start_time =  pyb.millis()
    current_time = 0
    n_cycles = 0
    clock.init(freq=1000)
    clock.callback(_clock_tick)
    # Run--------------------------------
    running = True
    for state_machine in state_machines:
        state_machine._start()
    if duration: # Run for finite time.
        end_time = current_time + duration * second
        while ((current_time - end_time) < 0) and running:            
            _update()
    else:
        while running:
            _update()
    # Post run---------------------------
    running = False
    clock.deinit()
    for state_machine in state_machines:
        state_machine._stop()  
    while data_output_queue.available():
        output_data(data_output_queue.get())
    print('N cycles: {}'.format(n_cycles))