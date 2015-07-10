from experiments import experiments
from boxes import Boxes
import datetime
from pprint import pformat
import os
from config import *

date = datetime.date.today().strftime('-%Y-%m-%d')

print('Experiments available:\n')

for i, exp in enumerate(experiments):
  print('\nExperiment number : {}  Name:  {}\n'.format(i, exp.name))
  for bx in exp.subjects:
    print('    Box : {}   '.format(bx) + exp.subjects[bx])

experiment = experiments[int(input('\n\nEnter which experiment to run: '))]

boxes_to_use = experiment.subjects.keys()

file_names = {box_n: experiment.subjects[box_n] + date + '.txt' for box_n in boxes_to_use}

boxes = Boxes(boxes_to_use, experiment.hardware)

if input('\nReload framework? (y / n)\n') == 'y':
    boxes.load_framework()

if input('\nRun hardware test? (y / n)\n') == 'y':
    print('Uploading hardware test.')
    boxes.setup_state_machine('hardware_test')
    boxes.start_framework(data_output = False)
    input('\nPress any key when finished with hardware test.\n')
    boxes.stop_framework()
else:
    print('Skipping hardware test.\n')

print('Uploading task.\n')

boxes.setup_state_machine(experiment.task)

if experiment.set_variables: # Set state machine variables from experiment specification.
    print('\nSetting state machine variables.\n')
    for v_name in experiment.set_variables:
        boxes.set_variable(experiment.task, v_name, experiment.set_variables[v_name])

if experiment.persistent_variables:
    pv_file_path = os.path.join(data_dir, experiment.folder, 'persistent_variables.txt')
    if os.path.exists(pv_file_path):
        print('\nSetting persistent variables.\n')
        with open(pv_file_path, 'r') as pv_file:
            persistent_v_values = eval(pv_file.read())
        for v_name in persistent_v_values.keys():
            boxes.set_variable(experiment.task, v_name, persistent_v_values[v_name])
    else:
        print('\nPersistent variables not set as persistent_variables.txt does not exist.\n')

boxes.open_data_file(file_names, sub_dir = experiment.folder)
boxes.print_IDs() # Print state and event information to file.

input('\nHit enter to start experiment. To quit at any time, hit ctrl + c.\n\n')

boxes.write_to_file('Run started at: ' + datetime.datetime.now().strftime('%H:%M:%S' + '\n\n'))

boxes.start_framework(dur = None, verbose = True)

try:
    while True:  # Read data untill interupted by user.
        boxes.process_data()
    
except KeyboardInterrupt:
    boxes.stop_framework()
    boxes.close_data_file()

    if experiment.persistent_variables:
        print('\nStoring persistent variables.\n')
        persistent_v_values = {}
        for v_name in experiment.persistent_variables:
            persistent_v_values[v_name] = boxes.get_variable(experiment.task, v_name)
            with open(pv_file_path, 'w') as pv_file:
                pv_file.write(pformat(persistent_v_values))
    
    boxes.close()
    # !! transfer files as necessary.
















