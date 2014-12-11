import pyb
from array import array

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
        self.events[None]    = None # Make event dict return None if None used to index.

        self.check_valid_IDs()

        self._ID2name = {ID:event for event, ID # Dict mapping IDs to event names.
                                   in list(self.events.items()) + list(self.states.items())}

        self.pc = PyControl # Pointer to framework.
        self.ID  = self.pc.register_machine(self)
        if hardware:
            hardware.set_machine(self)

    def start(self):
        # Called when run is started.
        # Puts agent in initial state, and runs entry event.
        self.state = self.initial_state
        self.process_event('entry')

    def stop(self):
        # Called at end of run. Overwrite with desired
        # functionality when state machines are defined.
        pass

    def set_timer(self, event, interval):
        self.pc.timer.set(self.events[event], int(interval), self.ID)

    def process_event_ID(self, event_ID):
        # Process event given event ID
        self.process_event(self._ID2name[event_ID])

    def process_event(self, event):
        # Process event given event name. Overwrite with desired
        # functionality when state machines are defined.
        pass

    def goto(self, next_state):
        self.process_event('exit')
        self.state = next_state
        self.process_event('entry')
        self.pc.data_output_queue.put((self.ID, self.states[next_state], self.pc.current_time))

    def check_valid_IDs(self):
        # Check that there are no repeated state or events IDs.
        all_ID2name = list(self.events.values()) + list(self.states.values())
        unique_ID2name = set(all_ID2name)
        if len(unique_ID2name) < len(all_ID2name):
            print('Error: State and event IDs must be unique.')


    def print_ID2name(self):
        # Print event and state dictionaries.
        print('Events:')
        for event in self.events:
            if event and self.events[event] > 0: # Print only user defined events.
                print(str(self.events[event]) + ': ' + event)
        print('States:')
        for state in self.states:
            print(str(self.states[state]) + ': ' + state)
