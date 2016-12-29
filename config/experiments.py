from cli.experiment  import *

# A simple example showing the minimal set of arguments needed to define an experiment.
simple_exp = Experiment(
          name = 'simple_experiment',    
          start_date = '2016-12-01',
          subjects = {1: 'm001',
                      2: 'm002'},
          task = 'random_ratio'
                       )

# A more complex example showing how additional arguments can be used.
example_exp = Experiment(
          name = 'example_experiment',    
          start_date = '2016-12-01',
          subjects = {1: 'm003',
                      2: 'm004'},
          task = 'reversal_learning',
          set_variables = {'session_duration':  2*hour,      # Set 'session_duration' to same value for all setups.
                           'reward_durations': {1:[80,90],   # Set 'reward_duration' to individual value for each setup.
                                                2:[75,85]}
                           },
          persistent_variables = ['state'], # Make variable 'state' persistant across sessions.
          summary_variables = ['n_rewards', # Display value of variables 'n_rewards' and 'n_trials' 
                               'n_trials',  # at end of session, copy values to clipboard with 
                                2]          # 2 blank lines between different variables.
                        )