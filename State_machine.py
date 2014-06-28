from PyControl import Event_queue
import pyb

# ----------------------------------------------------------------------------------------
# Units
# ----------------------------------------------------------------------------------------

minute = 60000
second = 1000
ms = 1

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
        self.reset()

    def reset(self):
        # Resets agent to initial state, with single entry event in que.
        self.current_state = self.initial_state
        self.event_queue.reset()  
        self.event_queue.put(self.events['entry']) 

    def update(self):
        if self.event_queue.available():
            self.process_event(self._ID2event[self.event_queue.get()[0]])

    def set_timer(self, event, interval):
        self.timer.set(self.events[event], int(interval))

    def process_event(self, event):
        pass

    def goto_state(self, next_state):
        self.process_event('exit')
        self.current_state = next_state
        self.process_event('entry')


