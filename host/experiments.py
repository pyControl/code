from experiment  import Experiment
from calibration import calibration

exp_1 = Experiment(
          name = 'example_experiment',    
          start_date = '2015-07-02',
          subjects = {1: 'm001',
                      2: 'm002'},
          task = 'blinker',
          # set_variables = {'LED_n' :  4,
          #                  'period': {1: 0.1,
          #                             2: 0.5} 
          #                 }
          persistent_variables = ['period']
          )



exp_two_step = Experiment(
          name = 'Two_step_experiment',    
          start_date = '2015-07-02',
          subjects = {1: 'm001',
                      2: 'm002'},
          task = 'two_step_full',
          hardware = "hw.Box()",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  True,
                                                          'high_reward_contrast':  True},
                           'reward_delivery_durations':calibration['large']},
          persistent_variables = ['outcome_generator.state']
          )



experiments = [exp_1, exp_two_step]


