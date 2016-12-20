from CLI.experiment  import *

example_exp = Experiment(
          name = 'Example_experiment',    
          start_date = '2016-12-01',
          subjects = {1: 'm001',
                      2: 'm002'},
          task = 'reversal_learning',
          set_variables = {'session_duration':  2*hour,      # Set 'session_duration' to same value for all setups.
                           'reward_durations': {1:[80,90],   # Set 'reward_duration' to individual value for each setup.
                                                2:[75,85]}
                           },
          persistent_variables = ['state'],  # Make variable 'state' persistant across sessions.
          summary_data = ['n_rewards',       # Display value of variables 'n_rewards' and 'n_trials' at end 
                          'n_trials', 2]     #  of session, copy values to clipboard with 2 blank lines 
          )                                  #  between different variables.  