import pyb

def random():
    #Return a random float between 0 and 1.
    return pyb.rng()/1073741824.

def withprob(p):
    # Return a random boolean that is True with probability p.
    return pyb.rng()<(1073741824. * p)

def mean(x):
    # Return the mean value of x.
    return(sum(x)/len(x))

