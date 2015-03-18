from State_machine import *

class Button(State_machine):
  
    states= {'LED_on'  :  1,
             'LED_off' :  2}

    events = {'button_event' :  3,
              'timer_event'  :  4}

    initial_state = 'LED_off'

    def __init__(self, PyControl, poke):

        self.poke = poke

        # Setup hardware events.
        self.poke.set_events('button_event')

        # Run state machine init.
        State_machine.__init__(self, PyControl, poke)

    # State event handler functions.

    def LED_on(self, event):
            if event == 'entry':
                self.set_timer('timer_event', 2 * second)
                self.poke.LED.on()
            elif event == 'exit':
                self.poke.LED.off()
            elif event == 'timer_event':
                self.goto('LED_off')
            elif event == 'button_event':
                self.goto('LED_off')

    def LED_off(self, event):
            if event == 'button_event':
                self.goto('LED_on')

    def stop(self):
        self.poke.LED.off()

