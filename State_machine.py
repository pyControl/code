import pyb
from array import array

ID_null_value =  0  # Event ID null value.

# ----------------------------------------------------------------------------------------
# Units
# ----------------------------------------------------------------------------------------

minute = 60000
second = 1000
ms = 1

# ----------------------------------------------------------------------------------------
# Event ID Queue
# ----------------------------------------------------------------------------------------

class Event_queue():
    #  Queue for holding events IDs.

    def __init__(self, buffer_length = 10):      
        self.buffer_length = buffer_length
        self.reset()

    def reset(self):
        # Empty queue, set IDs to null value.
        self.ID_buffer = array('i', [ID_null_value] * self.buffer_length)
        self.read_index  = 0
        self.write_index = 0

    def put(self, event_ID):
        # Put event ID in que.
        assert self.ID_buffer[self.write_index] == ID_null_value, 'Buffer full'
        self.ID_buffer[self.write_index] = event_ID          
        self.write_index = (self.write_index + 1) % self.buffer_length

    def get(self):
        # Get event from buffer.  If no events are available return event with null ID.
        event_ID = self.ID_buffer[self.read_index]
        self.ID_buffer[self.read_index] = ID_null_value
        if event_ID != ID_null_value:
            self.read_index = (self.read_index + 1) % self.buffer_length
        return (event_ID)

    def available(self):
        # Return true if buffer contains events.
        return self.ID_buffer[self.read_index] != ID_null_value


# ----------------------------------------------------------------------------------------
# State Machine
# ----------------------------------------------------------------------------------------

class State_machine():

    def __init__(self):
        self.event_queue = Event_queue() # Create event que.
        # Setup event dictionaries:
        self.events['entry'] = -1 # add entry and exit events to dictionary.
        self.events['exit' ] = -2 
        self._ID2event = {ID:event for event, ID # Dict mapping IDs to event names.
                                   in self.events.items()}
        self.ID    = None # Overwritten when machine is registered to framework.
        self.timer = None # Overwritten when machine is registered to framework.
        self.reset()

    def reset(self):
        # Resets agent to initial state, with single entry event in que.
        self.current_state = self.initial_state
        self.event_queue.reset()  
        self.event_queue.put(self.events['entry']) 

    def update(self):
        if self.event_queue.available():
            self.process_event(self._ID2event[self.event_queue.get()])

    def set_timer(self, event, interval):
        self.timer.set(self.events[event], int(interval))

    def process_event(self, event):
        pass

    def goto_state(self, next_state):
        self.process_event('exit')
        self.current_state = next_state
        self.process_event('entry')


