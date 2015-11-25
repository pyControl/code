from experiment  import Experiment
from config.calibration import calibration

example_exp = Experiment(
          name = 'example_experiment',    
          start_date = '2015-00-00',
          subjects = {1: 'm001'},
                      2: 'm002'},
          task = 'two_step',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  True,
                                                          'high_trans_contrast' :  True,
                                                          'high_reward_contrast':  True},
                           'reward_delivery_durations':calibration['large']},
          persistent_variables = ['outcome_generator.state']
          )




