class Experiment:
    'Class used to hold information about an experiment'
    def __init__(self, name, start_date, subjects, task, hardware = None,
                 set_variables = None, persistent_variables = None, folder = None):
      ''' Arguments:
      subjects : dict specifying the ID of the subject run in each box.
      set_variables:  dict specifying variables whose values should be 
                      modified from defaults in script.  A dict of box numbers
                      and values can be provided as a variable to set variable 
                      differently for each box.
      persistant_variables:  list of variables whose values should be persistant
                             from session to session. 
      folder:  name of data folder, defaults to start_date + name.
      '''
      self.name = name      
      self.start_date = start_date     
      self.subjects = subjects   
      self.task = task
      self.hardware = hardware
      self.set_variables = set_variables
      self.persistent_variables = persistent_variables
      if folder:
        self.folder = folder
      else:
        self.folder = start_date + '-' + name
