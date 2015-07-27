from experiment  import Experiment
from calibration import calibration


exp_pilot_1 = Experiment(
          name = 'JAWS_ACC_pilot',    
          start_date = '2015-07-09',
          subjects = {1: 'm263',
                      2: 'm264'},
          task = 'two_step_full_opto',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['pilot']},
          persistent_variables = ['outcome_generator.state'],
          )

exp_pilot_2 = Experiment(
          name = 'JAWS_ACC_pilot',    
          start_date = '2015-07-09',
          subjects = {3: 'm265',
                      4: 'm266'},
          task = 'two_step_full_opto',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['pilot']},
          persistent_variables = ['outcome_generator.state'],
          )

exp_pilot_3 = Experiment(
          name = 'JAWS_ACC_pilot',    
          start_date = '2015-07-09',
          subjects = {5: 'm267',
                      6: 'm268'},
          task = 'two_step_full_opto',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['pilot']},
          persistent_variables = ['outcome_generator.state'],
          )

exp_pilot_4 = Experiment(
          name = 'JAWS_ACC_pilot',    
          start_date = '2015-07-09',
          subjects = {7: 'm290',
                      8: 'm286'},
          task = 'two_step_full_opto',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['pilot']},
          persistent_variables = ['outcome_generator.state'],
          )


exp_main = Experiment(
          name = 'JAWS_ACC_main',    
          start_date = '2015-07-09',
          subjects = {1:  'm299',
                      2:  'm300',
                      3:  'm301',
                      4:  'm302',
                      5:  'm303',
                      6:  'm304',
                      7:  'm305',
                      8:  'm306',
                      9:  'm307',
                      10: 'm308',
                      11: 'm309',
                      12: 'm310',
                      13: 'm311',
                      14: 'm312'},
          task = 'two_step_full',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['main']},
          persistent_variables = ['outcome_generator.state']
          )

exp_test = Experiment(
          name = 'Test',    
          start_date = '2015-00-00',
          subjects = {14: 'm312'},
          task = 'two_step_full_opto',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  True,
                                                          'high_reward_contrast':  True},
                           'reward_delivery_durations':calibration['large']},
          persistent_variables = ['outcome_generator.state']
          )

experiments = [exp_pilot_1, exp_pilot_2, exp_pilot_3, exp_pilot_4, exp_main, exp_test]


