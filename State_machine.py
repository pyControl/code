# ----------------------------------------------------------------------------------------
# State Machine
# ----------------------------------------------------------------------------------------

from PyControl import *

class State_machine():

    def __init__(self):
        self.ID = register_machine(self) # Register with framework.
        self.event_queue = Event_queue() # Create event que.
        # Setup event dictionaries:
        self.events['entry'] = -1 # add entry and exit events to dictionary.
        self.events['exit' ] = -2 
        self._ID2event = {ID:event for event, ID 
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
        timer.set(self.events[event], int(interval))

    def process_event(self, event):
        pass

    def goto_state(self, next_state):
        self.process_event('exit')
        self.current_state = next_state
        self.process_event('entry')


# ----------------------------------------------------------------------------------------
# Blinker example.
# ----------------------------------------------------------------------------------------


class blinker(State_machine):

    states= {'LED_on'  :  1,
             'LED_off' :  2}

    events = {'timer_evt' :  3}

    initial_state = 'LED_off'

    def process_event(self, event):

        if   self.current_state == 'LED_on':

            if event == 'entry':
                self.set_timer('timer_evt', 1 * second)
                print('LED_on')

            elif event == 'exit':
                print('LED_off')

            elif event == 'timer_evt':
                self.goto_state('LED_off')

        elif self.current_state == 'LED_off':

            if event == 'entry':
                self.set_timer('timer_evt', 0.5 * second)

            if event == 'timer_evt':
                self.goto_state('LED_on')


