import pyb

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

# ----------------------------------------------------------------------------------------
# Units.
# ----------------------------------------------------------------------------------------

minute = 60000
second = 1000
ms = 1

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