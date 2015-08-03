from experiment  import Experiment
from .calibration import calibration


exp_test = Experiment(
          name = 'Test',    
          start_date = '2015-00-00',
          subjects = {1: 'm312'},
          task = 'two_step_full_opto',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  True,
                                                          'high_reward_contrast':  True},
                           'reward_delivery_durations':calibration['large']},
          persistent_variables = ['outcome_generator.state']
          )


exp_test2 = Experiment(
          name = 'Test2',    
          start_date = '2015-00-00',
          subjects = {1: 'm312'},
          task = 'two_step_full_opto',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  True,
                                                          'high_reward_contrast':  True},
                           'reward_delivery_durations':calibration['large']},
          persistent_variables = ['outcome_generator.state']
          )


