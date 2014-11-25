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
# Timer_array
# ----------------------------------------------------------------------------------------

class timer_array():

    def __init__(self, n_timers = 10):
        self.n_timers = n_timers  
        self.timer_set = False # Variable used in set() fuction.
        self.reset()

    def reset(self):
        global current_time
        current_time = pyb.millis()
        self.start_time = current_time
        self.event_IDs           = array('i', [ID_null_value] * self.n_timers)
        self.trigger_times = array('L', [0]  * self.n_timers)
        self.machine_IDs   = array('i', [-1] * self.n_timers)

    def set(self, event_ID, interval, machine_ID):
        # Set a timer to trigger with specified event ID after 'interval' ms has elapsed.
        global current_time
        self.timer_set = False
        self.index = 0
        while not self.timer_set:
            if self.event_IDs[self.index] == ID_null_value:
                self.event_IDs[self.index] = event_ID
                self.trigger_times[self.index] = current_time + interval
                self.machine_IDs[self.index] = machine_ID
                self.timer_set = True
            if self.index >= self.n_timers:
                print('ERROR: insufficient timers available, increase n_timers.')
            self.index += 1

    def check(self):
        #Check whether any timers have triggered and place corresponding events into 
        # event que
        global current_time
        for self.index in range(self.n_timers):
            if self.event_IDs[self.index] != ID_null_value and \
               ((current_time - self.trigger_times[self.index]) >= 0):
               publish_event((self.machine_IDs[self.index], self.event_IDs[self.index], current_time))
               self.event_IDs[self.index] = ID_null_value


# ----------------------------------------------------------------------------------------
# Framework variables and objects
# ----------------------------------------------------------------------------------------

state_machines = []  # List to hold state machines.

hardware = []          # List to hold hardware objects.
 
timer = timer_array()  # Instantiate timer_array object.

event_queue = Event_queue() # Instantiate event que object.

interrupts_waiting = False # Set true if interrupt waiting to be processed.


# ----------------------------------------------------------------------------------------
# Framework functions.
# ----------------------------------------------------------------------------------------

def register_machine(state_machine):
        machine_ID = len(state_machines)
        state_machines.append(state_machine)
        return machine_ID

def register_hardware(boxIO):
    hardware.append(boxIO)

def publish_event(event):    
    event_queue.put(event)

def _update():
    # Perform framework update functions in order of priority.
    global current_time, interrupts_waiting
    current_time = pyb.millis()
    timer.check() 
    if interrupts_waiting:
        interrupts_waiting = False
        for boxIO in hardware:
            if boxIO.interrupt_triggered:
                boxIO.process_interrupt()
    elif event_queue.available():
        event = event_queue.get()
        if event[0] == -1: # Publish event to all machines.
            for state_machine in state_machines:
                state_machine.process_event_ID(event[1])
        else:
            state_machines[event[0]].process_event_ID(event[1])

def run_machines(duration):
    # Pre run----------------------------
    global current_time
    timer.reset()
    end_time = timer.start_time + duration
    for state_machine in state_machines:
        state_machine.start()
    # Run--------------------------------
    while (current_time - end_time) < 0:            
        _update()
    # Post run---------------------------
    for state_machine in state_machines:
        state_machine.stop()  









