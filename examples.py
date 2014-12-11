from State_machine import *

# ----------------------------------------------------------------------------------------
# Blinker example.
# ----------------------------------------------------------------------------------------

class Blinker(State_machine):

    # Class variables.

    states= {'LED_on'  :  1,
             'LED_off' :  2}

    events = {'timer_evt' :  3}

    initial_state = 'LED_off'

        
    def __init__(self, PyControl, LED = 1, period = 1.):
        # Instance variables.
        self.LED = pyb.LED(LED)
        self.period = period

        State_machine.__init__(self, PyControl)

    def process_event(self, event):

        if   self.state == 'LED_on':

            if event == 'entry':
                self.set_timer('timer_evt', self.period * second)
                self.LED.on()

            elif event == 'exit':
                self.LED.off()

            elif event == 'timer_evt':
                self.goto('LED_off')

        elif self.state == 'LED_off':

            if event == 'entry':
                self.set_timer('timer_evt', self.period * second)

            if event == 'timer_evt':
                self.goto('LED_on')

    def stop(self):
        self.LED.off()


class Button(State_machine):

        
    states= {'LED_on'  :  1,
             'LED_off' :  2}

    events = {'button_event' :  3,
              'timer_event'  :  4}

    initial_state = 'LED_off'

    def __init__(self, PyControl, poke, LED = 1):
        self.poke = poke
        # Setup hardware events.
        self.poke.set_events('button_event')

        # Run state machine init.
        State_machine.__init__(self, PyControl, poke)

    def process_event(self, event):

        if   self.state == 'LED_on':

            if event == 'entry':
                self.set_timer('timer_event', 500 * ms)
                self.poke.LED_on()

            elif event == 'timer_event':
                if self.poke.get_state():
                    self.poke.SOL_on()

            elif event == 'exit':
                self.poke.LED_off()
                self.poke.SOL_off()

            elif event == 'button_event':
                self.goto('LED_off')

        elif self.state == 'LED_off':

            if event == 'button_event':
                self.goto('LED_on')

    def stop(self):
        self.poke.LED_off()
        self.poke.SOL_off()



