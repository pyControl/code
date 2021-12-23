# Module imported by the user into their task file which contains the 
# functions, classes and variables used in task files.

import pyb
import math
from . import framework as fw

# State machine functions -----------------------------------------------------

def goto_state(next_state):
    fw.state_machine.goto_state(next_state)

def timed_goto_state(next_state, interval):
    # Transition to next_state after interval milliseconds. timed_goto_state()
    # is cancelled if goto_state() occurs before interval elapses.
    fw.timer.set(interval, fw.state_typ, fw.states[next_state])

def set_timer(event, interval, output_event=False):
    # Set a timer to return specified event after interval milliseconds.
    event_type = fw.event_typ if output_event else fw.timer_typ
    fw.timer.set(interval, event_type, fw.events[event])    

def disarm_timer(event):
    # Disable all timers due to return specified event.
    fw.timer.disarm(fw.events[event])

def reset_timer(event, interval, output_event=False):
    # Disarm all timers due to return specified event and set new timer
    # to return specified event after interval milliseconds.
    fw.timer.disarm(fw.events[event])
    event_type = fw.event_typ if output_event else fw.timer_typ
    fw.timer.set(interval, event_type, fw.events[event])

def pause_timer(event):
    # Pause all timers due to return specified event.
    fw.timer.pause(fw.events[event])

def unpause_timer(event):
    # Unpause all timers due to return specified event.
    fw.timer.unpause(fw.events[event])

def timer_remaining(event):
    # Return time until timer for specified event elapses, returns 0 if no timer set for event.
    return fw.timer.remaining(fw.events[event])

def print(print_string):
    # Used to output data print_string with timestamp.  print_string is stored and only
    #  printed to serial line once higher priority tasks have all been processed. 
    if fw.data_output:
        fw.data_output_queue.put((fw.current_time, fw.print_typ, str(print_string)))

def publish_event(event):
    # Put event with specified name in the event queue.
    fw.event_queue.put((fw.current_time, fw.event_typ, fw.events[event]))

def stop_framework():
    fw.running = False

def get_current_time():
    return fw.current_time

#  Random functions and classes -----------------------------------------------

max_rand = 1 << 30 # Largest number output by pyb.rng()

def random():
    #Return a random float x such that 0 <= x < 1.
    return pyb.rng()/max_rand

def withprob(p):
    # Return a random boolean that is True with probability p.
    return pyb.rng()<(max_rand * p)

def shuffled(L):
    # Return a shuffled copy of list L.
    return sorted(L, key = lambda l: pyb.rng())

def randint(a,b):  
  # Return a random integer N such that a <= N <= b.
    return int(a+(b+1-a)*random())

def choice(L):
    # Return a randomly selected item from list L.
    return L[randint(0,len(L)-1)]

def exp_rand(m):
    #  Return an exponentially distributed random number with mean m.
    return -math.log(1.-random())*m

def gauss_rand(m,s):
    # Return a gaussian distributed random number with mean m and standard deviation s.
    return m+s*(math.sqrt(-2.*math.log(random()))*math.cos(2*math.pi*random()))

class sample_without_replacement:
    # Repeatedly sample elements from items list without replacement.
    def __init__(self, items):
        self._all_items = items
        self._next_items = [] + shuffled(items)

    def next(self):
        if len(self._next_items) == 0:
            self._next_items += shuffled(self._all_items)
        return self._next_items.pop()

#  Math functions and classes -------------------------------------------------

def mean(x):
    # Return the mean value of x.
    return(sum(x)/len(x))

class exp_mov_ave:
    # Exponential moving average class.
    def __init__(self, tau, init_value=0):
        self.tau = tau
        self.init_value = init_value
        self.reset()

    def reset(self, init_value=None, tau=None):
        if tau:
            self.tau = tau
        if init_value:
            self.init_value = init_value
        self.value = self.init_value
        self._m = math.exp(-1./self.tau)
        self._i = 1 - self._m

    def update(self, sample):
        self.value = (self.value * self._m) + (self._i * sample)

# Units -----------------------------------------------------------------------

ms     = const(1)
second = const(1000*ms)
minute = const(60*second)
hour   = const(60*minute)

# Variables class -------------------------------------------------------------

class variables():
    # Class for holding task variables.  Acts as single namespace used by all
    # state behaviour functions.  Also lets GUI know where variables are for setting/getting.
    def __init__(self):
        pass

v = variables()