import pyb
import math

# ----------------------------------------------------------------------------------------
# Utility functions.
# ----------------------------------------------------------------------------------------

def random():
    #Return a random float between 0 and 1.
    return pyb.rng()/1073741824.

def withprob(p):
    # Return a random boolean that is True with probability p.
    return pyb.rng()<(1073741824. * p)

def shuffled(L):
    # Return a shuffled copy of list L.
    return sorted(L, key = lambda l: pyb.rng())

def randint(a,b):  
  # Return a random integer N such that a <= N <= b.
    return int(a+(b+1-a)*random())

def mean(x):
    # Return the mean value of x.
    return(sum(x)/len(x))

# ----------------------------------------------------------------------------------------
# Utility classes
# ----------------------------------------------------------------------------------------

class exp_mov_ave:
    # Exponential moving average class.
    def __init__(self, tau, init_value):
        self.tau = tau
        self.init_value = init_value
        self.reset()

    def reset(self, init_value = None, tau = None):
        if tau:
            self.tau = tau
        if init_value:
            self.init_value = init_value
        self.value = self.init_value
        self._m = math.exp(-1./self.tau)
        self._i = 1 - self._m

    def update(self, sample):
        self.value = (self.value * self._m) + (self._i * sample)


class sample_without_replacement:
    # Repeatedly sample elements from items list without replacement.
    def __init__(self, items):
        self._all_items = items
        self._next_items = [] + shuffled(items)

    def next(self):
        if len(self._next_items) == 0:
            self._next_items += shuffled(self._all_items)
        return self._next_items.pop()

# ----------------------------------------------------------------------------------------
# Units.
# ----------------------------------------------------------------------------------------

ms = 1
second = 1000
minute = 60 * second
hour = 60 * minute

# ----------------------------------------------------------------------------------------
# Variables class.
# ----------------------------------------------------------------------------------------

class variables():
    # Class for holding task variables.  Acts as single namespace used by all
    # state behaviour functions.  Also lets GUI know where variables are for setting/getting.
    def __init__(self):
        pass

v = variables()