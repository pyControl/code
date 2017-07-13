import pyb
import math

# ----------------------------------------------------------------------------------------
#  Random functions and classes.
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

def choice(L):
    # Return a randomly selected item from list L.
    return L[randint(0,len(L)-1)]

def exp_rand(m):
    #  Return an exponentially distributed random number with mean m.
    return -math.log(1.-random())*m

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
#  Math functions and classes
# ----------------------------------------------------------------------------------------

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

# ----------------------------------------------------------------------------------------
# Units.
# ----------------------------------------------------------------------------------------

ms     = const(1)
second = const(1000*ms)
minute = const(60*second)
hour   = const(60*minute)

# ----------------------------------------------------------------------------------------
# Variables class.
# ----------------------------------------------------------------------------------------

class variables():
    # Class for holding task variables.  Acts as single namespace used by all
    # state behaviour functions.  Also lets GUI know where variables are for setting/getting.
    def __init__(self):
        pass

v = variables()