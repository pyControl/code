from state_machine import *

class Button(State_machine):
  
    states= {'LED_on'  :  1,
             'LED_off' :  2}

    events = {'button_event' :  3,
              'timer_event'  :  4}

    initial_state = 'LED_off'

    # State event handler functions.

    def LED_on(self, event):
            if event == 'entry':
                self.set_timer('timer_event', 2 * second)
                self.hw.LED.on()
            elif event == 'exit':
                self.hw.LED.off()
            elif event == 'timer_event':
                self.goto('LED_off')
            elif event == 'button_event':
                self.goto('LED_off')

    def LED_off(self, event):
            if event == 'button_event':
                self.goto('LED_on')

    def stop(self):
        self.hw.LED.off()

