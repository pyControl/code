from experiment  import Experiment
#from calibration import calibration


exp_pilot = Experiment(
          name = 'JAWS_ACC_pilot',    
          start_date = '2015-07-09',
          subjects = {1: 'm263',
                      2: 'm264',
                      3: 'm265',
                      4: 'm266',
                      5: 'm267',
                      6: 'm268',
                      7: 'm290',
                      8: 'm286'},
          task = 'two_step_full',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  True,
                                                          'high_trans_contrast' :  True,
                                                          'high_reward_contrast':  True}},#,
                           #'reward_delivery_durations':calibration['large']},
          persistent_variables = ['outcome_generator.state']
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
          set_variables = {'outcome_generator.settings': {'first_session'       :  True,
                                                          'high_trans_contrast' :  True,
                                                          'high_reward_contrast':  True}},#,
                          # 'reward_delivery_durations':calibration['large']},
          persistent_variables = ['outcome_generator.state']
          )

experiments = [exp_pilot, exp_main]


