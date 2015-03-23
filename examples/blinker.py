from state_machine import *

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

    def LED_on(self, event):
        if event == 'entry':
            self.set_timer('timer_evt', self.period * second)
            self.LED.on()
        elif event == 'exit':
            self.LED.off()
        elif event == 'timer_evt':
            self.goto('LED_off')

    def LED_off(self, event):
        if event == 'entry':
            self.set_timer('timer_evt', self.period * second)
        elif event == 'timer_evt':
            self.goto('LED_on')

    def stop(self):
        self.LED.off()





