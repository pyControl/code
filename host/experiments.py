from experiment import Experiment

exp_1 = Experiment(
          name = 'example_experiment',    
          start_date = '2015-07-02',
          subjects = {1: 'm001',
                      2: 'm002'},
          task = 'blinker')

experiments = [exp_1]