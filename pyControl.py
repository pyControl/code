from array import array
import pyb

ID_null_value =  0  # Event ID null value, no event may have this ID.

# ----------------------------------------------------------------------------------------
# Event Que
# ----------------------------------------------------------------------------------------

class Event_queue():
    #  Queue for holding event tuples: (machine_ID, event_ID, timestamp)
    def __init__(self, buffer_length = 20):
        self.buffer_length = buffer_length
        self.reset()

    def reset(self):
        # Empty queue, set IDs to null value.
        self.ID_buffer = array('i', [ID_null_value] * self.buffer_length)
        self.TS_buffer = array('L', [0]  * self.buffer_length)
        self.SM_buffer = array('i', [-1] * self.buffer_length)
        self.read_index  = 0
        self.write_index = 0

    def put(self, event):
        # Put event in que.  
        assert self.ID_buffer[self.write_index] == ID_null_value, 'Buffer full'
        self.SM_buffer[self.write_index] = event[0] 
        self.ID_buffer[self.write_index] = event[1]
        self.TS_buffer[self.write_index] = event[2]      
        self.write_index = (self.write_index + 1) % self.buffer_length

    def get(self):
        # Get event from buffer.  If no events are available return None.
        event_ID   = self.ID_buffer[self.read_index]
        timestamp  = self.TS_buffer[self.read_index] 
        machine_ID = self.SM_buffer[self.read_index] 
        self.ID_buffer[self.read_index] = ID_null_value
        if event_ID != ID_null_value:
            self.read_index = (self.read_index + 1) % self.buffer_length
            return (machine_ID, event_ID, timestamp)
        else:
            return None

    def available(self):
        # Return true if buffer contains events.
        return self.ID_buffer[self.read_index] != ID_null_value

# ----------------------------------------------------------------------------------------
# Timer
# ----------------------------------------------------------------------------------------

class Timer():

    def __init__(self):
        self.timer_set = False # Variable used in set() fuction.
        self.reset()

    def reset(self):
        self.active_timers = [] # list of tuples: (trigger_time, machine_ID, event_ID)

    def set(self, event_ID, interval, machine_ID):
        # Set a timer to trigger with specified event ID after 'interval' ms has elapsed.
        global current_time
        trigger_time = current_time + interval
        self.active_timers.append((trigger_time, machine_ID, event_ID))

    def check(self):
        #Check whether any timers have triggered and place corresponding events into 
        # event que.
        global current_time
        for i,active_timer in enumerate(self.active_timers):
            if current_time - active_timer[0] >= 0:
                publish_event((active_timer[1], active_timer[2], current_time), output_data = False)
                self.active_timers.pop(i)

# ----------------------------------------------------------------------------------------
# Framework variables and objects
# ----------------------------------------------------------------------------------------

state_machines = []  # List to hold state machines.

hardware = []          # List to hold hardware objects.
 
timer = Timer()  # Instantiate timer_array object.

event_queue = Event_queue() # Instantiate event que object.

interrupts_waiting = False # Set true if interrupt waiting to be processed.

data_output_queue = Event_queue() # Queue used for outputing events to serial line.

output_data = True  # Whether to output data to the serial line.

verbose = False     # True: output names, False: output IDs

current_time = None # Time since run started (milliseconds).

start_time = 0      # Time when run was started.

# ----------------------------------------------------------------------------------------
# Framework functions.
# ----------------------------------------------------------------------------------------

def register_machine(state_machine):
        machine_ID = len(state_machines)
        state_machines.append(state_machine)
        return machine_ID

def register_hardware(boxIO):
    hardware.append(boxIO)

def publish_event(event, output_data = True):    
    event_queue.put(event) # Publish to state machines.
    if output_data:        # Publish to serial output.
        data_output_queue.put(event)

def output_data(event):
    # Output data to serial line.
    event_name = state_machines[event[0]]._ID2name[event[1]]
    if event_name == 'dprint': # Print user generated output string.
        print('{} {} '.format(event[2], event[0]) + state_machines[event[0]].dprint_queue.pop(0))
    else:  # Print event or state change.
        if verbose: # Print event/state name.
            print('{} {} '.format(event[2], event[0]) + event_name)
        else: # Print event/state ID.
            print('{} {} {}'.format(event[2], event[0], event[1]))

def _update():
    # Perform framework update functions in order of priority.
    global current_time, interrupts_waiting, start_time
    current_time = pyb.elapsed_millis(start_time)
    timer.check() 
    if interrupts_waiting:         # Priority 1: Process interrupts.
        interrupts_waiting = False
        for boxIO in hardware:
            if boxIO.interrupt_triggered:
                boxIO._process_interrupt()
    elif event_queue.available():  # Priority 2: Process events in queue.
        event = event_queue.get()
        if event[0] == -1: # Publish event to all machines.
            for state_machine in state_machines:
                state_machine._process_event_ID(event[1])
        else:
            state_machines[event[0]]._process_event_ID(event[1])
    elif data_output_queue.available(): # Priority 3: Output data.
        output_data(data_output_queue.get())
        

def run_machines(duration):
    # Pre run----------------------------
    global current_time
    global start_time
    timer.reset()
    event_queue.reset()
    data_output_queue.reset()
    for boxIO in hardware:
        boxIO.reset()
    start_time =  pyb.millis()
    current_time = 0
    end_time = current_time + duration
    for state_machine in state_machines:
        state_machine._start()
    # Run--------------------------------
    while (current_time - end_time) < 0:            
        _update()
    # Post run---------------------------
    for state_machine in state_machines:
        state_machine.stop()  









