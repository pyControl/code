import config.experiments as exps
from experiment import Experiment
from config.config import *
from boxes import Boxes
import datetime
from pprint import pformat
from sys import exit
import os

def config_menu():
    print('\nOpening connection to all boxes listed in config.py.\n\n')
    boxes = Boxes(box_serials.keys())
    selection = None
    while selection != 3:
        selection = int(input('''\n\nConfig menu:
                                 \n\n 1. Reload framwork.
                                 \n\n 2. Save hardware IDs.
                                 \n\n 3. Exit config menu.
                                 \n\n 4. Close program.\n\n'''))
        if selection == 1:
            boxes.load_framework()
        elif selection == 2:
            boxes.save_unique_IDs()
        elif selection == 4:
            boxes.close()
            exit()
    boxes.close()

# Create list of available experiments

experiments = [e for e in [getattr(exps, c) for c in dir(exps)]
               if isinstance(e, Experiment)] # Construct list of available experiments.

date = datetime.date.today().strftime('-%Y-%m-%d')

selection = 0
while selection == 0: 

    print('\nExperiments available:\n')

    for i, exp in enumerate(experiments):
      print('\nExperiment number : {}  Name:  {}\n'.format(i + 1, exp.name))
      for bx in exp.subjects:
        print('    Box : {}   '.format(bx) + exp.subjects[bx])

    selection = int(input('\n\nEnter number of experiment to run, for config options enter 0: \n'))
    if selection == 0:
        config_menu()

experiment = experiments[selection - 1]

boxes_to_use = list(experiment.subjects.keys())

file_names = {box_n: experiment.subjects[box_n] + date + '.txt' for box_n in boxes_to_use}

boxes = Boxes(boxes_to_use, experiment.hardware)

if not boxes.check_unique_IDs():
    input('Hardware ID check failed, press any key to close program.')
    boxes.close()
    exit()

if input('\nRun hardware test? (y / n)\n') == 'y':
    print('Uploading hardware test.')
    boxes.setup_state_machine('hardware_test')
    boxes.start_framework(data_output = False)
    input('\nPress any key when finished with hardware test.\n')
    boxes.stop_framework()
else:
    print('Skipping hardware test.\n')

print('Uploading task.\n')

boxes.setup_state_machine(experiment.task, tasks_dir)

if experiment.set_variables: # Set state machine variables from experiment specification.
    print('\nSetting state machine variables.\n')
    for v_name in experiment.set_variables:
        boxes.set_variable(experiment.task, v_name, experiment.set_variables[v_name])

if experiment.persistent_variables:
    pv_file_path = os.path.join(data_dir, experiment.folder,
                               'persistent_variables_{}.txt'.format(boxes_to_use[0]))
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

boxes.write_to_file('Run started at: ' + datetime.datetime.now().strftime('%H:%M:%S') + '\n\n')

boxes.start_framework(dur = None, verbose = False)

try:
    boxes_running = True
    while boxes_running:  # Read data untill interupted by user.
        boxes_running = boxes.process_data()
    
except KeyboardInterrupt:
    boxes.stop_framework()

boxes.close_data_file(copy_to_transfer = True)

if experiment.persistent_variables:
    print('\nStoring persistent variables.\n')
    persistent_v_values = {}
    for v_name in experiment.persistent_variables:
        persistent_v_values[v_name] = boxes.get_variable(experiment.task, v_name)
        with open(pv_file_path, 'w') as pv_file:
            pv_file.write(pformat(persistent_v_values))

boxes.close()

input('\nHit any key to close program.')
    # !! transfer files as necessary.
















