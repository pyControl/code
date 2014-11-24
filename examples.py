from State_machine import *

# ----------------------------------------------------------------------------------------
# Blinker example.
# ----------------------------------------------------------------------------------------

class Blinker(State_machine):

    # Class variables.

    states= {'LED_on'  :  1,
             'LED_off' :  2}

    events = {'timer_evt' :  1}

    initial_state = 'LED_off'

        
    def __init__(self, PyControl, LED = 1, period = 1.):
        # Instance variables.
        self.LED = pyb.LED(LED)
        self.period = period

        State_machine.__init__(self, PyControl)

    def process_event(self, event):

        if   self.current_state == 'LED_on':

            if event == 'entry':
                self.set_timer('timer_evt', self.period * second)
                print('LED_on')
                self.LED.on()

            elif event == 'exit':
                print('LED_off')
                self.LED.off()

            elif event == 'timer_evt':
                self.goto_state('LED_off')

        elif self.current_state == 'LED_off':

            if event == 'entry':
                self.set_timer('timer_evt', self.period * second)

            if event == 'timer_evt':
                self.goto_state('LED_on')

    def stop(self):
        self.LED.off()


class Button(State_machine):

        
    states= {'LED_on'  :  1,
             'LED_off' :  2}

    events = {'button_event' :  1}

    initial_state = 'LED_off'

    def __init__(self, PyControl, LED = 1):
        # Instance variables.
        self.LED = pyb.LED(LED)
        State_machine.__init__(self, PyControl)

    def process_event(self, event):

        if   self.current_state == 'LED_on':

            if event == 'entry':
                print('LED_on')
                self.LED.on()

            elif event == 'exit':
                print('LED_off')
                self.LED.off()

            elif event == 'button_event':
                self.goto_state('LED_off')

        elif self.current_state == 'LED_off':

            if event == 'button_event':
                self.goto_state('LED_on')

    def stop(self):
        self.LED.off()

