from . import utility
from . import framework as fw


class State_machine():
    # State machine behaviour is defined by passing state machine description object smd to 
    # State_machine __init__(). smd is a module which defines the states, events and  
    # functionality of the state machine object that is created (see examples). 

    def __init__(self, smd):

        self.smd = smd # State machine definition.
        self.variables = utility.v # User task variables object.
        self.state_transition_in_progress = False # Set to True during state transitions.

        fw.register_machine(self)

        # Make dict mapping state names to state event handler functions.
        smd_methods = dir(self.smd) # List of methods of state machine instance.
        self.event_dispatch_dict = {}
        for state in list(self.smd.states) + ['all_states', 'run_start', 'run_end']:
            if state in smd_methods:
                self.event_dispatch_dict[state] = getattr(self.smd, state)
            else:
                self.event_dispatch_dict[state] = None

    def goto_state(self, next_state):
        # Transition to next state, calling exit action of old state
        # and entry action of next state.
        if self.state_transition_in_progress:
            raise fw.pyControlError("goto_state cannot not be called while processing 'entry' or 'exit' events.")
        if not next_state in self.smd.states.keys():
            raise fw.pyControlError('Invalid state name passed to goto_state: ' + repr(next_state))
        self.state_transition_in_progress = True
        self._process_event('exit')
        fw.timer.disarm_type(fw.state_typ) # Clear any timed_goto_states     
        if fw.data_output:
            fw.data_output_queue.put((fw.current_time, fw.state_typ, fw.states[next_state]))
        self.current_state = next_state
        self._process_event('entry')
        self.state_transition_in_progress = False

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
            fw.data_output_queue.put((fw.current_time, fw.state_typ, fw.states[self.current_state]))
        self._process_event('entry')

    def _stop(self):
        # Calls user defined stop function at end of run if function is defined.
        if self.event_dispatch_dict['run_end']:
            self.event_dispatch_dict['run_end']()

    def _set_variable(self, v_name, v_str, checksum=None):
        # Set value of variable v.v_name to value eval(v_str).
        if checksum:
            str_sum = sum(v_str) if type(v_str) is bytes else sum(v_str.encode())
            if not str_sum == checksum:
                return False # Bad checksum.
        try:
            setattr(self.variables, v_name, eval(v_str))
            return True # Variable set OK.
        except Exception:
            return False # Bad variable name or invalid value string.

    def _get_variable(self, v_name):
        try:
            return repr(getattr(self.variables, v_name))
        except Exception:
            return None