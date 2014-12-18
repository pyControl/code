import pyb
from array import array
from utility import *

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

    def __init__(self, PyControl, hardware = None):
        # Setup event dictionaries:
        self.events['entry'] = -1 # add entry and exit events to dictionary.
        self.events['exit' ] = -2 

        self._check_valid_IDs()

        self._ID2name = {ID:event for event, ID # Dict mapping IDs to event names.
                                   in list(self.events.items()) + list(self.states.items())}

        self.pc = PyControl # Pointer to framework.
        self.ID  = self.pc.register_machine(self)
        if hardware:
            hardware.set_machine(self)

    # Methods called by user.


    def process_event(self, event):
        # Process event given event name. Overwrite with desired
        # functionality when state machines are defined.
        pass

    def goto(self, next_state):
        # Transition to new state, calling exit action of old state
        # and entry action of new state.
        self.process_event('exit')
        self.state = next_state
        self.pc.data_output_queue.put((self.ID, self.states[next_state], self.pc.current_time))
        self.process_event('entry')

    def set_timer(self, event, interval):
        # Set a timer to return specified event afterinterval milliseconds.
        self.pc.timer.set(self.events[event], int(interval), self.ID)

    def stop(self):
        # Called at end of run. Overwrite with desired
        # functionality when state machines are defined.
        pass

    # Methods called by PyControl framework.

    def _start(self):
        # Called when run is started.
        # Puts agent in initial state, and runs entry event.
        self.state = self.initial_state
        self.pc.data_output_queue.put((self.ID, self.states[self.state], self.pc.current_time))
        self.process_event('entry')

    def _process_event_ID(self, event_ID):
        # Process event given event ID
        self.process_event(self._ID2name[event_ID])

    def _check_valid_IDs(self):
        # Check that there are no repeated state or events IDs.
        all_IDs = list(self.events.values()) + list(self.states.values())
        unique_IDs = set(all_IDs)
        if len(unique_IDs) < len(all_IDs):
            print('Error: States and events must have unique IDs.')
        for ID in all_IDs:
            if not type(ID) == int:
                print('Error: Event and state IDs must be integers.')

    def _print_ID2name(self):
        # Print event and state dictionaries.
        print('Events:')
        for event in self.events:
            if event and self.events[event] > 0: # Print only user defined events.
                print(str(self.events[event]) + ': ' + event)
        print('States:')
        for state in self.states:
            print(str(self.states[state]) + ': ' + state)
