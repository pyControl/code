from experiment  import Experiment
from config.calibration import calibration

example_exp = Experiment(
          name = 'Example_experiment',    
          start_date = '2015-11-15',
          subjects = {1:  'm001'},
          task = 'two_step',
          set_variables = {'outcome_generator.settings': {'first_session'       :  True,
                                                          'high_trans_contrast' :  True,
                                                          'high_reward_contrast':  True},
                           'reward_delivery_durations':calibration['large']},
          persistent_variables = ['outcome_generator.state'],
          summary_data = ['outcome_generator.reward_number',
                          'outcome_generator.block_number' , 4]
          )

