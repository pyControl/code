from experiment  import Experiment
from config.calibration import calibration


# exp_pilot_1 = Experiment(
#           name = 'JAWS_ACC_pilot',    
#           start_date = '2015-07-09',
#           subjects = {1: 'm263',
#                       2: 'm264'},
#           task = 'two_step_full_opto',
#           hardware = "hw.Box('bkb')",
#           set_variables = {'outcome_generator.settings': {'first_session'       :  False,
#                                                           'high_trans_contrast' :  False,
#                                                           'high_reward_contrast':  False},
#                            'reward_delivery_durations':calibration['pilot']},
#           persistent_variables = ['outcome_generator.state'],
#           )

# exp_pilot_2 = Experiment(
#           name = 'JAWS_ACC_pilot',    
#           start_date = '2015-07-09',
#           subjects = {3: 'm265',
#                       4: 'm266'},
#           task = 'two_step_full_opto',
#           hardware = "hw.Box('bkb')",
#           set_variables = {'outcome_generator.settings': {'first_session'       :  False,
#                                                           'high_trans_contrast' :  False,
#                                                           'high_reward_contrast':  False},
#                            'reward_delivery_durations':calibration['pilot']},
#           persistent_variables = ['outcome_generator.state'],
#           )

# exp_pilot_3 = Experiment(
#           name = 'JAWS_ACC_pilot',    
#           start_date = '2015-07-09',
#           subjects = {5: 'm267',
#                       6: 'm268'},
#           task = 'two_step_full_opto',
#           hardware = "hw.Box('bkb')",
#           set_variables = {'outcome_generator.settings': {'first_session'       :  False,
#                                                           'high_trans_contrast' :  False,
#                                                           'high_reward_contrast':  False},
#                            'reward_delivery_durations':calibration['pilot']},
#           persistent_variables = ['outcome_generator.state'],
#           )

# exp_pilot_4 = Experiment(
#           name = 'JAWS_ACC_pilot',    
#           start_date = '2015-07-09',
#           subjects = {7: 'm290',
#                       8: 'm286'},
#           task = 'two_step_full_opto',
#           hardware = "hw.Box('bkb')",
#           set_variables = {'outcome_generator.settings': {'first_session'       :  False,
#                                                           'high_trans_contrast' :  False,
#                                                           'high_reward_contrast':  False},
#                            'reward_delivery_durations':calibration['pilot']},
#           persistent_variables = ['outcome_generator.state'],
#           )

exp_main_1 = Experiment(
          name = 'JAWS_ACC_main',    
          start_date = '2015-07-09',
          subjects = {1:  'm299',
                      2:  'm300'},
          task = 'two_step_full_opto_II',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['main']},
          persistent_variables = ['outcome_generator.state']
          )

exp_main_2 = Experiment(
          name = 'JAWS_ACC_main',    
          start_date = '2015-07-09',
          subjects = {3:  'm301',
                      4:  'm302'},
          task = 'two_step_full_opto_II',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['main']},
          persistent_variables = ['outcome_generator.state']
          )

exp_main_3 = Experiment(
          name = 'JAWS_ACC_main',    
          start_date = '2015-07-09',
          subjects = {5:  'm303',
                      6:  'm304'},
          task = 'two_step_full_opto_II',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['main']},
          persistent_variables = ['outcome_generator.state']
          )

exp_main_4 = Experiment(
          name = 'JAWS_ACC_main',    
          start_date = '2015-07-09',
          subjects = {7:  'm305',
                      8:  'm306'},
          task = 'two_step_full_opto_II',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['main']},
          persistent_variables = ['outcome_generator.state']
          )

exp_main_5 = Experiment(
          name = 'JAWS_ACC_main',    
          start_date = '2015-07-09',
          subjects = {9:  'm307',
                      10: 'm308'},
          task = 'two_step_full_opto_II',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['main']},
          persistent_variables = ['outcome_generator.state']
          )

exp_main_6 = Experiment(
          name = 'JAWS_ACC_main',    
          start_date = '2015-07-09',
          subjects = {11: 'm309',
                      12: 'm310'},
          task = 'two_step_full_opto_II',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['main']},
          persistent_variables = ['outcome_generator.state']
          )

exp_main_7 = Experiment(
          name = 'JAWS_ACC_main',    
          start_date = '2015-07-09',
          subjects = {13: 'm311',
                      14: 'm312'},
          task = 'two_step_full_opto_II',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['main']},
          persistent_variables = ['outcome_generator.state']
          )

# exp_main = Experiment(
#           name = 'JAWS_ACC_main',    
#           start_date = '2015-07-09',
#           subjects = {1:  'm299',
#                       2:  'm300',
#                       3:  'm301',
#                       4:  'm302',
#                       5:  'm303',
#                       6:  'm304',
#                       7:  'm305',
#                       8:  'm306',
#                       9:  'm307',
#                       10: 'm308',
#                       11: 'm309',
#                       12: 'm310',
#                       13: 'm311',
#                       14: 'm312'},
#           task = 'two_step_full_opto',
#           hardware = "hw.Box('bkb')",
#           set_variables = {'outcome_generator.settings': {'first_session'       :  False,
#                                                           'high_trans_contrast' :  False,
#                                                           'high_reward_contrast':  False},
#                            'reward_delivery_durations':calibration['main']},
#           persistent_variables = ['outcome_generator.state']
#           )

exp_FOXp2_1 = Experiment(
          name = 'FOXp2_group_1',    
          start_date = '2015-08-05',
          subjects = {1 : 'm313',
                      2 : 'm314',
                      3 : 'm315',
                      4 : 'm316',
                      5 : 'm317',
                      6 : 'm318',
                      7 : 'm319',
                      8 : 'm320',
                      9 : 'm321',
                      10: 'm322',
                      11: 'm323',
                      12: 'm324',
                      13: 'm325',
                      14: 'm326'},
          task = 'two_step_full',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['small'],
                           'session_duration':5400000,
                           'outcome_generator.mean_neutral_block_length': 65},
          persistent_variables = ['outcome_generator.state']
          )

exp_FOXp2_2 = Experiment(
          name = 'FOXp2_group_2',    
          start_date = '2015-08-05',
          subjects = {1 : 'm327',
                      2 : 'm328',
                      3 : 'm329',
                      4 : 'm330',
                      5 : 'm331',
                      6 : 'm332',
                      7 : 'm333',
                      8 : 'm334',
                      9 : 'm335',
                      10: 'm336',
                      11: 'm337',
                      12: 'm338',
                      13: 'm339',
                      14: 'm340'},
          task = 'two_step_full',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['small'],
                           'session_duration':5400000,
                           'outcome_generator.mean_neutral_block_length': 65},
          persistent_variables = ['outcome_generator.state']
          )

exp_FOXp2_3 = Experiment(
          name = 'FOXp2_group_3',    
          start_date = '2015-08-05',
          subjects = {7 : 'm341',
                      8 : 'm342',
                      9 : 'm343',
                      10: 'm344',
                      11: 'm345',
                      12: 'm346',
                      13: 'm347',
                      14: 'm348'},
          task = 'two_step_full',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.settings': {'first_session'       :  False,
                                                          'high_trans_contrast' :  False,
                                                          'high_reward_contrast':  False},
                           'reward_delivery_durations':calibration['small'],
                           'session_duration':5400000,
                           'outcome_generator.mean_neutral_block_length': 65},
          persistent_variables = ['outcome_generator.state']
          )

exp_one_step_pilot = Experiment(
          name = 'One_step',    
          start_date = '2015-08-15',
          subjects = {1 : 'm349',
                      2 : 'm350',
                      3 : 'm351',
                      4 : 'm352',
                      5 : 'm353',
                      6 : 'm354'},
          task = 'one_step',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.first_session': False,
                           'reward_delivery_durations':calibration['medium']},
          persistent_variables = ['outcome_generator.reward_state',
                                  'hold_generator.hold_dur',
                                  'hold_generator.mov_ave.ave']
          )

exp_one_step_main = Experiment(
          name = 'One_step_main',    
          start_date = '2015-08-15',
          subjects = {1 : 'm355',
                      2 : 'm356',
                      3 : 'm357',
                      4 : 'm362',
                      5 : 'm358',
                      6 : 'm359',
                      7 : 'm360',
                      8 : 'm361',
                      9 : 'm363',
                      10: 'm364',
                      11: 'm365',
                      12: 'm366',
                      13: 'm367',
                      14: 'm368'},
          task = 'one_step',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.first_session': False,
                           'reward_delivery_durations':calibration['large']},
          persistent_variables = ['outcome_generator.reward_state',
                                  'hold_generator.hold_dur',
                                  'hold_generator.mov_ave.ave']
          )

exp_test = Experiment(
          name = 'Test',    
          start_date = '2015-00-00',
          subjects = {1: 'm353'},
                      #14: 'm354'},
          task = 'one_step',
          hardware = "hw.Box('bkb')",
          set_variables = {'outcome_generator.first_session': False,
                           'reward_delivery_durations':calibration['large']},
          persistent_variables = ['outcome_generator.reward_state',
                                  'hold_generator.hold_dur',
                                  'hold_generator.mov_ave.ave']
          )




