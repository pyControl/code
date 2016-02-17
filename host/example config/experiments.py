from experiment  import Experiment
from config.calibration import calibration

example_exp = Experiment(
          name = 'Example_experiment',    
          start_date = '2015-11-15',
          subjects = {1:  'm001'},
          task = 'two_step',
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['main']},
          persistent_variables = ['outcome_generator.state']
          )

