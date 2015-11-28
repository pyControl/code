import pyb
from array import array
from . import framework as fw
from .utility import *

# ----------------------------------------------------------------------------------------
# State Machine
# ----------------------------------------------------------------------------------------

class State_machine():
    # State machine behaviour is defined by passing state machine description object smd to 
    # State_machine __init__(). smd is a module which defines the states, events and  
    # functionality of the state machine object that is created (see examples). 

    def __init__(self, smd):

        self.smd = smd # State machine definition.

        fw.register_machine(self)

        self._make_event_dispatch_dict()

        # Attach user functions to discription object namespace, this allows the user to write e.g.
        # goto(state) in the task description to call State_machine goto function. 
        smd.goto           = self.goto
        smd.set_timer      = self.set_timer
        smd.disarm_timer   = self.disarm_timer
        smd.print          = self.print 
        smd.stop_framework = self.stop_framework  

    # Methods used in __init__

    def _make_event_dispatch_dict(self):
        # Makes a dictionary mapping state names to state event handler functions used by _process_event.
        methods = dir(self.smd) # List of methods of state machine instance.
        self.event_dispatch_dict = {}
        for state in list(self.smd.states) + ['all_states', 'run_start', 'run_end']:
            if state in methods:
                self.event_dispatch_dict[state] = getattr(self.smd, state)
            else:
                self.event_dispatch_dict[state] = None

    # Methods called by user.

    def goto(self, next_state):
        # Transition to new state, calling exit action of old state
        # and entry action of new state.
        self._process_event('exit')
        self.current_state = next_state
        if fw.data_output:
            fw.data_output_queue.put((fw.states[next_state], fw.current_time))
        self._process_event('entry')

    def set_timer(self, event, interval):
        # Set a timer to return specified event after interval milliseconds.
        fw.timer.set(fw.events[event], int(interval))

    def disarm_timer(self, event):
        # Disable all active timers due to return specified event.
        fw.timer.disarm(fw.events[event])

    def print(self, print_string):
        # Used to output data print_string with timestamp.  print_string is stored and only
        #  printed to serial line once higher priority tasks have all been processed. 
        if fw.data_output:
            fw.print_queue.append(print_string)
            fw.data_output_queue.put((-1, fw.current_time)) # Code -1 is used to indicate print string event to output_data.

    def stop_framework(self):
        fw.running = False

    # Methods called by pyControl framework.

    def _process_event(self, event):
        # Process event given event name by calling appropriate state event handler function.
        if self.event_dispatch_dict['all_states']:                      # If machine has all_states event handler function. 
            handled = self.event_dispatch_dict['all_states'](event)     # Evaluate all_states event handler function.
            if handled: return                                          # If all_states event handler returns True, don't evaluate state specific behaviour.
        if self.event_dispatch_dict[self.current_state]:                # If state machine has event handler function for current state.
            self.event_dispatch_dict[self.current_state](event)         # Evaluate state event handler function.

    def _start(self):
        # Called when run is started. Puts agent in initial state, and runs entry event.
        if self.event_dispatch_dict['run_start']:
            self.event_dispatch_dict['run_start']()
        self.current_state = self.smd.initial_state
        if fw.data_output:
            fw.data_output_queue.put((fw.states[self.current_state], fw.current_time))
        self._process_event('entry')

    def _stop(self):
        # Calls user defined stop function at end of run if function is defined.
        if self.event_dispatch_dict['run_end']:
            self.event_dispatch_dict['run_end']()





