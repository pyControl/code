import pyb
import pyControl as pc
from array import array
from utility import *

# ----------------------------------------------------------------------------------------
# State Machine
# ----------------------------------------------------------------------------------------

class State_machine():
    # State machine behaviour is defined by passing state machine description object sm to 
    # State_machine constructor. sm is a module which defines the states, events and  
    # functionality of the state machine  object that is created (see examples). 

    def __init__(self, sm, hardware = None):

        self.sm = sm
        self.events = sm.events
        self.states = sm.states
        self.initial_state = sm.initial_state

        if type(self.events) == list and type(self.states) == list:
            self._assign_IDs()
        elif not (type(self.events) == dict and type(self.states) == dict):
            print('Error: events and states must both be lists or both be dicts.') 

        # Setup event dictionaries:
        self.events['entry']  = -1 # add framework (non user defined) events to dictionary.
        self.events['exit' ]  = -2 
        self.events['dprint'] = -3

        self._check_valid_IDs()

        self._ID2name = {ID:event for event, ID # Dict mapping IDs to event names.
                                   in list(self.events.items()) + list(self.states.items())}

        self._make_event_dispatch_dict(sm)

        self.dprint_queue = [] # Queue for strings output using dprint function. 

        self.ID  = pc.register_machine(self)

        self.sm.hw = hardware
        if hardware:
            hardware.set_machine(self)

        # Attach user functions to discription object namespace, this allows the user to write e.g.
        # goto('state_1') in the task description to access State_machine goto function. 
        sm.goto      = self.goto
        sm.set_timer = self.set_timer
        sm.dprint    = self.dprint  

    # Methods called by user.

    def goto(self, next_state):
        # Transition to new state, calling exit action of old state
        # and entry action of new state.
        self._process_event('exit')
        self.sm.state = next_state
        pc.data_output_queue.put((self.ID, self.states[next_state], pc.current_time))
        self._process_event('entry')

    def set_timer(self, event, interval):
        # Set a timer to return specified event afterinterval milliseconds.
        pc.timer.set(self.events[event], int(interval), self.ID)

    def dprint(self, print_string):
        # Used to output data 'print_string', along with ID of originating machine and timestamp.
        # 'print_string' is stored and only printed to serial line once higher priority events 
        # (e.g. interupt handling, state changes) have all been processed.
        if pc.output_data:
            self.dprint_queue.append(print_string)
            pc.data_output_queue.put((self.ID, self.events['dprint'], pc.current_time))

    # Methods called by pyControl framework.

    def _process_event(self, event):
        # Process event given event name by calling appropriate state event handler method.
        if self.event_dispatch_dict['all_states']:                      # If machine has all_states event handler method. 
            handled = self.event_dispatch_dict['all_states'](event)     # Evaluate all_states event handler method.
            if (not handled) and self.event_dispatch_dict[self.sm.state]:  # If all_states does not return handled = True and machine has state event handler method.
                self.event_dispatch_dict[self.sm.state](event)             # Evaluate state event handler method.
        elif self.event_dispatch_dict[self.sm.state]:
            self.event_dispatch_dict[self.sm.state](event)                 # Evaluate state event handler method.

    def _start(self):
        # Called when run is started.
        # Puts agent in initial state, and runs entry event.
        self.sm.state = self.initial_state
        pc.data_output_queue.put((self.ID, self.states[self.sm.state], pc.current_time))
        if self.event_dispatch_dict['run_start']:
            self.event_dispatch_dict['run_start']()
        self._process_event('entry')

    def stop(self):
        # Calls user defined stop function at end of run if function is defined.
        if self.event_dispatch_dict['run_end']:
            self.event_dispatch_dict['run_end']()

    def _process_event_ID(self, event_ID):
        # Process event given event ID
        self._process_event(self._ID2name[event_ID])

    def _assign_IDs(self):
        # If states and events are specified as list of names, 
        # convert to dict of {names: IDs}.
        n_states = len(self.states) 
        state_IDs = list(range(1, n_states + 1))
        event_IDs = list(range(n_states + 1, n_states + len(self.events) + 1))
        self.states = dict(zip(self.states, state_IDs))
        self.events = dict(zip(self.events, event_IDs))

    def _check_valid_IDs(self):
        # Check that there are no repeated state or events IDs.
        all_IDs = list(self.events.values()) + list(self.states.values())
        unique_IDs = set(all_IDs)
        if len(unique_IDs) < len(all_IDs):
            print('Error: States and events must have unique IDs.')
        for ID in all_IDs:
            if not type(ID) == int:
                print('Error: Event and state IDs must be integers.')

    def _print_IDs(self):
        # Print event and state IDs
        print('States:')
        for state_ID in sorted(self.states.values()):
            print(str(state_ID) + ': ' + self._ID2name[state_ID])
        print('Events:')
        for event_ID in sorted(self.events.values()):
            if event_ID > 0: # Print only user defined events.
                print(str(event_ID) + ': ' + self._ID2name[event_ID])

    def _make_event_dispatch_dict(self, sm):
        # Makes a dictionary mapping state names to state event handler functions used by _process_event.
        methods = dir(sm) # List of methods of state machine instance.
        self.event_dispatch_dict = {}
        for state in list(self.states.keys()) + ['all_states', 'run_start', 'run_end']:
            if state in methods:
                self.event_dispatch_dict[state] = getattr(sm, state)
            else:
                self.event_dispatch_dict[state] = None



