from State_machine import *

# ----------------------------------------------------------------------------------------
# Blinker example.
# ----------------------------------------------------------------------------------------

class blinker(State_machine):

    states= {'LED_on'  :  1,
             'LED_off' :  2}

    events = {'timer_evt' :  1}

    initial_state = 'LED_off'

    LED = pyb.LED(1)
    

    def __init__(self):
        State_machine.__init__(self)

    def process_event(self, event):


        if   self.current_state == 'LED_on':

            if event == 'entry':
                self.set_timer('timer_evt', 1 * second)
                print('LED_on')
                self.LED.on()

            elif event == 'exit':
                print('LED_off')
                self.LED.off()

            elif event == 'timer_evt':
                self.goto_state('LED_off')

        elif self.current_state == 'LED_off':

            if event == 'entry':
                self.set_timer('timer_evt', 1 * second)

            if event == 'timer_evt':
                self.goto_state('LED_on')


