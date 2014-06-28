from array import array
import pyb


# ----------------------------------------------------------------------------------------
# Event Que
# ----------------------------------------------------------------------------------------

class Event_queue():
    #  Queue for holding events consisting of an event ID and timestamp.

    def __init__(self, buffer_length = 10):
        self.ID_null_value =  0  # ID null value.
        self.TS_null_value =  0  # Time stamp null value.       
        self.buffer_length = buffer_length
        self.reset()

    def reset(self):
        # Empty queue, set IDs to null value.
        self.ID_buffer = array('i', [self.ID_null_value] * self.buffer_length)
        self.TS_buffer = array('L', [self.TS_null_value] * self.buffer_length)
        self.read_index  = 0
        self.write_index = 0

    def put(self, event):
        # Put event in que.  If event in an int, it is treated as the event ID and a 
        # timestamp is generated.  event can also be an (ID, timestamp) tuple .
        assert self.ID_buffer[self.write_index] == self.ID_null_value, 'Buffer full'
        if isinstance(event, int):
            self.ID_buffer[self.write_index] = event
            self.TS_buffer[self.write_index] = pyb.millis()
        else:
            self.ID_buffer[self.write_index] = event[0]
            self.TS_buffer[self.write_index] = event[1]            
        self.write_index = (self.write_index + 1) % self.buffer_length

    def get(self):
        # Get event from buffer.  If no events are available return event with null ID.
        ID = self.ID_buffer[self.read_index]
        timestamp =  self.TS_buffer[self.read_index] 
        self.ID_buffer[self.read_index] = self.ID_null_value
        self.TS_buffer[self.read_index] = self.TS_null_value
        if ID != self.ID_null_value:
            self.read_index = (self.read_index + 1) % self.buffer_length
        return (ID, timestamp)

    def available(self):
        # Return true if buffer contains events.
        return self.ID_buffer[self.read_index] != self.ID_null_value

# ----------------------------------------------------------------------------------------
# Timer_array
# ----------------------------------------------------------------------------------------

class timer_array():

    def __init__(self, n_timers = 10):
        self.n_timers = n_timers
        self.ID_null_value = -1  # ID null value.    
        self.triggered_events = Event_queue(n_timers)
        self.timer_set = False # Variable used in set() fuction.
        self.reset()

    def reset(self):
        self.IDs = array('i', [self.ID_null_value] * self.n_timers)
        self.trigger_times = array('L', [0] * self.n_timers)
        self.index  = 0
        self.max_active = 0 
        self.triggered_events.reset()

    def set(self, ID, interval, current_time = None):
        # Set a timer to trigger with specified event ID after 'interval' ms has elapsed.
        if not current_time:
            current_time = pyb.millis()
        self.timer_set = False
        self.index = 0
        while not self.timer_set:
            if self.IDs[self.index] == self.ID_null_value:
                self.IDs[self.index] = ID
                self.trigger_times[self.index] = current_time + interval
                self.timer_set = True
            if self.index >= self.n_timers:
                print('ERROR: insufficient timers available, increase n_timers.')
            self.index += 1

    def check(self, current_time = None):
        #Check whether any timers have triggered and place corresponding events into 
        # triggered_events buffer.
        if not current_time:
            current_time = pyb.millis()
        for self.index in range(self.n_timers):
            if self.IDs[self.index] != self.ID_null_value and \
               ((current_time - self.trigger_times[self.index]) >= 0):
               self.triggered_events.put((self.IDs[self.index], current_time))
               self.IDs[self.index] = self.ID_null_value
        return self.triggered_events.available()

# ----------------------------------------------------------------------------------------
# Framework variables and objects
# ----------------------------------------------------------------------------------------

state_machines = []  # List to hold state machines.
 
timer = timer_array()  # Instantiate timer_array object.

# ----------------------------------------------------------------------------------------
# Framework functions.
# ----------------------------------------------------------------------------------------

def register_machine(state_machine):
    machine_ID = len(state_machines)
    state_machines.append(state_machine)
    state_machine.ID = machine_ID
    state_machine.timer = timer

def publish_event(event_ID):
    # Put event in queue's of all state machines.
    for state_machine in state_machines:
        state_machine.event_queue.put(event_ID)

def _update():
    # Check timers and publish timer events.
    if timer.check(): 
        while timer.triggered_events.available():
            publish_event(timer.triggered_events.get())
    # Update state machines
    for state_machine in state_machines:
        state_machine.update()

def run_machines(cycles):
    for state_machine in state_machines:
        state_machine.reset()
        timer.reset()
    for i in range(cycles):
        _update()







