# ----------------------------------------------------------------------------------------
# State Machine
# ----------------------------------------------------------------------------------------

from PyControl import *

class State_machine():

    def __init__(self):
        self.ID = register_machine(self) # Register with framework.
        self.event_queue = Event_queue()
        self.current_state = self.initial_state
         # Reverse dictionary for mapping event names to ID numbers.
        self._inv_events = {ID:event for event, ID in self.events.items()}

    def update(self):
        if self.event_queue.available():
            self.process_event(self._inv_events[self.event_queue.get()[0]])

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
                print('LED_on')

            elif event == 'exit':
                print('LED_off')

            elif event == 'timer_evt':
                self.set_timer('timer_evt', 1 * second)
                self.goto_state('LED_off')


        elif self.current_state == 'LED_off':

            if event == 'timer_evt':
                self.set_timer('timer_evt', 0.5 * second)
                self.goto_state('LED_on')

