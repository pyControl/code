import pyb
from array import array
from PyControl import ID_null_value

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
        # Setup event dictionaries:
        self.events['entry'] = -1 # add entry and exit events to dictionary.
        self.events['exit' ] = -2 
        self._ID2event = {ID:event for event, ID # Dict mapping IDs to event names.
                                   in self.events.items()}
        self.ID    = None # Overwritten when machine is registered to framework.
        self.timer = None # Overwritten when machine is registered to framework.

    def start(self):
        # Puts agent in initial state, with single entry event in que.
        # Called by framework when run is started.
        self.current_state = self.initial_state
        self.process_event('entry')

    def set_timer(self, event, interval):
        self.timer.set(self.events[event], int(interval), self.ID)

    def process_event_ID(self, event_ID):
        # Process event given event ID
        self.process_event(self._ID2event[event_ID])

    def process_event(self, event):
        # Process event given event name. Overwritten with desired
        # functionality when state machines are defined.
        pass

    def goto_state(self, next_state):
        self.process_event('exit')
        self.current_state = next_state
        self.process_event('entry')



