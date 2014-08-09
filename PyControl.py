from array import array
import pyb

# ----------------------------------------------------------------------------------------
# Event Que
# ----------------------------------------------------------------------------------------

class Event_queue():
    #  Queue for holding event tuples: (machine_ID, event_ID, timestamp, )
    def __init__(self, buffer_length = 10):
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
        # Get event from buffer.  If no events are available return event with null ID.
        event_ID   = self.ID_buffer[self.read_index]
        timestamp  = self.TS_buffer[self.read_index] 
        machine_ID = self.SM_buffer[self.read_index] 
        self.ID_buffer[self.read_index] = ID_null_value
        if event_ID != ID_null_value:
            self.read_index = (self.read_index + 1) % self.buffer_length
        return (machine_ID, event_ID, timestamp)

    def available(self):
        # Return true if buffer contains events.
        return self.ID_buffer[self.read_index] != ID_null_value

# ----------------------------------------------------------------------------------------
# Timer_array
# ----------------------------------------------------------------------------------------

class timer_array():

    def __init__(self, n_timers = 10):
        self.n_timers = n_timers  
        self.triggered_events = Event_queue(n_timers)
        self.timer_set = False # Variable used in set() fuction.
        self.reset()

    def reset(self):
        self.IDs           = array('i', [ID_null_value] * self.n_timers)
        self.trigger_times = array('L', [0]  * self.n_timers)
        self.machine_IDs   = array('i', [-1] * self.n_timers)
        self.triggered_events.reset()

    def set(self, ID, interval, machine_ID):
        # Set a timer to trigger with specified event ID after 'interval' ms has elapsed.
        global current_time
        self.timer_set = False
        self.index = 0
        while not self.timer_set:
            if self.IDs[self.index] == ID_null_value:
                self.IDs[self.index] = ID
                self.trigger_times[self.index] = current_time + interval
                self.machine_IDs[self.index] = machine_ID
                self.timer_set = True
            if self.index >= self.n_timers:
                print('ERROR: insufficient timers available, increase n_timers.')
            self.index += 1

    def check(self):
        #Check whether any timers have triggered and place corresponding events into 
        # triggered_events buffer.
        global current_time
        for self.index in range(self.n_timers):
            if self.IDs[self.index] != ID_null_value and \
               ((current_time - self.trigger_times[self.index]) >= 0):
               self.triggered_events.put((self.IDs[self.index], current_time, self.machine_IDs[self.index]))
               self.IDs[self.index] = ID_null_value
        return self.triggered_events.available()

# ----------------------------------------------------------------------------------------
# Framework variables and objects
# ----------------------------------------------------------------------------------------

state_machines = []  # List to hold state machines.
 
timer = timer_array()  # Instantiate timer_array object.

ID_null_value =  0  # Event ID null value, no event may have this ID.

global current_time



# ----------------------------------------------------------------------------------------
# Framework functions.
# ----------------------------------------------------------------------------------------

def register_machine(state_machine):
    machine_ID = len(state_machines)
    state_machines.append(state_machine)
    state_machine.ID = machine_ID
    state_machine.timer = timer

def publish_event(event):
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







