from State_machine import *

class Two_step(State_machine):

    states = {'pre_session'       : 1,
              'post_session'      : 2,
              'center_active'     : 3,
              'left_active'       : 4,
              'right_active'      : 5,
              'left_reward'       : 6,
              'right_reward'      : 7,
              'wait_for_poke_out' : 8,
              'inter_trial'       : 9}

    events = {'left_poke'        : 10, 
              'left_poke_out'    : 11,
              'right_poke'       : 12,
              'right_poke_out'   : 13,
              'high_poke'        : 14,
              'low_poke'         : 15,
              'session_timer'    : 16,
              'state_timer'      : 17,
              'session_start'    : 18,
              'session_stop'     : 19}

    initial_state = 'center_active'

    norm_prob = 0.8
    reward_probs = [0.2,0.8]

    def __init__(self, PyControl, box):

        self.box = box

        State_machine.__init__(self, PyControl, box)

    def process_event(self, event):

        # Events processed irrespective of state.

        if event == 'session_stop':
            self.goto('post_session')

        # State dependent event processing.

        elif self.state == 'pre_session':

            if event == 'session_start':
                self.goto('center_active')

            elif event == 'exit':
                self.box.houselight.on()


        elif self.state == 'post_session':

            if event == 'entry':
                self.box.houselight.off()           


        elif self.state == 'center_active':

            if event == 'entry':
                self.box.center_poke.LED.on()

            elif event == 'exit':
                self.box.center_poke.LED.off()

            elif event == 'high_poke':
                if withprob(self.norm_prob):
                    self.goto('left_active')
                else:
                    self.goto('right_active')

            elif event == 'low_poke':
                if withprob(self.norm_prob):
                    self.goto('right_active')
                else:
                    self.goto('left_active')


        elif self.state ==  'left_active':

            if event == 'entry':
                self.box.left_poke.LED.on()

            if event == 'exit':
                self.box.left_poke.LED.off()

            if event == 'left_poke':
                if withprob(self.reward_probs[0]):
                    self.goto('left_reward')
                else:
                    self.goto('wait_for_poke_out')


        elif self.state ==  'right_active':

            if event == 'entry':
                self.box.right_poke.LED.on()

            if event == 'exit':
                self.box.right_poke.LED.off()

            if event == 'right_poke':
                if withprob(self.reward_probs[1]):
                    self.goto('right_reward')
                else:
                    self.goto('wait_for_poke_out')


        elif self.state == 'left_reward':

            if event == 'entry':
                self.box.left_poke.SOL.on()
                self.set_timer('state_timer', 100 * ms)

            if event == 'exit':
                self.box.left_poke.SOL.off()

            if event == 'state_timer':
                self.goto('wait_for_poke_out')


        elif self.state ==  'right_reward':

            if event == 'entry':
                self.box.right_poke.SOL.on()
                self.set_timer('state_timer', 100 * ms)

            if event == 'exit':
                self.box.right_poke.SOL.off()

            if event == 'state_timer':
                self.goto('wait_for_poke_out')     
            

        elif self.state == 'wait_for_poke_out':

            if event == 'entry':
                if not (self.box.left_poke.get_state() or \
                        self.box.right_poke.get_state()):
                    self.goto('inter_trial') # Subject already left poke.

            if event in ['left_poke_out', 'right_poke_out']:
                self.goto('inter_trial')


        elif self.state == 'inter_trial':

            if event == 'entry':
                self.set_timer('state_timer', 1 * second)

            if event == 'state_timer':
                self.goto('center_active')

    def stop(self):
        self.box.off()








