from experiment import Experiment

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

experiments = [exp_1]