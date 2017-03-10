# Experiment class and constants used in specifying experiments.

class Experiment:
    'Class used to hold information about an experiment'
    def __init__(self, name, start_date, subjects, task, set_variables = None,
                 persistent_variables = None, folder = None, summary_variables = None):
      ''' Arguments:
      subjects : dict specifying the ID of the subject run on each board.
      set_variables:  dict specifying variables whose values should be 
                      modified from defaults in script.  A dict of board numbers
                      and values can be provided as a variable to set variable 
                      differently for each board.
      persistant_variables:  list of variables whose values should be persistant
                             from session to session. 
      folder:  name of data folder, defaults to start_date + name.
      '''
      self.name = name      
      self.start_date = start_date     
      self.subjects = subjects   
      self.task = task
      self.set_variables = set_variables
      self.persistent_variables = persistent_variables
      self.n_subjects = len(self.subjects.keys())
      self.summary_variables = summary_variables
      if folder:
        self.folder = folder
      else:
        self.folder = start_date + '-' + name

# ----------------------------------------------------------------------------------------
# Constants.
# ----------------------------------------------------------------------------------------

ms     = 1
second = 1000*ms
minute = 60*second
hour   = 60*minute
