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

def mean(x):
    # Return the mean value of x.
    return(sum(x)/len(x))

def shuffled(L):
    # Return a shuffled copy of list L.
    return sorted(L, key = lambda l: pyb.rng())

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
        self.ave = self.init_value
        self._m = math.exp(-1./self.tau)
        self._i = 1 - self._m

    def update(self, sample):
        self.ave = (self.ave * self._m) + (self._i * sample)

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
    # Class for holding task variables.  Main purpose is to create single scope shared 
    # across state behaviour functions to ensure that when variables are created or 
    # modified in one state this persists to other states. Will eventually have functionality
    # for outputting and modifying variables over serial.
    def __init__(self):
        pass

v = variables()