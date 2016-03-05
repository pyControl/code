import config.experiments as exps
from experiment import Experiment
import config.config as cf
from boxes import Boxes
import datetime
from pprint import pformat
from sys import exit
import os

# ----------------------------------------------------------------------------------------
# Helper functions.
# ----------------------------------------------------------------------------------------

def config_menu():
    print('\n\nOpening connection to all boxes listed in config.py.\n\n')
    boxes = Boxes(cf.box_serials.keys())
    selection = None
    while selection != 4:
        selection = int(input('''\n\nConfig menu:
                                 \n\n 1. Reload framwork.
                                 \n\n 2. Reload hardware definition.
                                 \n\n 3. Save hardware IDs.
                                 \n\n 4. Exit config menu.
                                 \n\n 5. Close program.\n\n'''))
        if selection == 1:
            boxes.load_framework()
        elif selection == 2:
            boxes.load_hardware_definition()
        elif selection == 3:
            boxes.save_unique_IDs()
        elif selection == 5:
            boxes.close()
            exit()
    boxes.close()

# ----------------------------------------------------------------------------------------
# Main program code.
# ----------------------------------------------------------------------------------------

# Create list of available experiments

if hasattr(exps,'experiments'):
    experiments = exps.experiments # List of experiments specified in experiments.py
else:
    experiments = [e for e in [getattr(exps, c) for c in dir(exps)]
                   if isinstance(e, Experiment)] # Construct list of available experiments.

date = datetime.date.today().strftime('-%Y-%m-%d')

selection = 0
while selection == 0: 

    print('\nExperiments available:\n')

    for i, exp in enumerate(experiments):
      print('\nExperiment number : {}  Name:  {}\n'.format(i + 1, exp.name))
      for box_n, subject_ID in exp.subjects.items():
        print('    Box : {}   {}'.format(box_n, subject_ID))

    selection = int(input('\n\nEnter number of experiment to run, for config options enter 0: '))
    if selection == 0:
        config_menu()

exp = experiments[selection - 1] # The selected experiment.

boxes_in_use = sorted(list(exp.subjects.keys()))
data_dir     = os.path.join(cf.data_dir, exp.folder)
file_paths   = {box_n: os.path.join(data_dir, exp.subjects[box_n] + date + '.txt')
                       for box_n in boxes_in_use}

print('')

boxes = Boxes(boxes_in_use)

if not boxes.check_unique_IDs():
    input('Hardware ID check failed, press any key to close program.')
    boxes.close()
    exit()

if input('\nRun hardware test? (y / n) ') == 'y':
    print('\nUploading hardware test.\n')
    boxes.setup_state_machine(cf.hardware_test)
    if cf.hardware_test_display_output:
        print('\nPress CTRL + C when finished with hardware test.\n')
        boxes.run_framework()
    else: 
        boxes.start_framework(data_output = False)
        input('\nPress any key when finished with hardware test.')
        boxes.stop_framework()
else:
    print('\nSkipping hardware test.')

print('\nUploading task.\n')

boxes.setup_state_machine(exp.task)

if exp.set_variables: # Set state machine variables from experiment specification.
    print('\nSetting state machine variables.')
    for v_name in exp.set_variables:
        boxes.set_variable(v_name, exp.set_variables[v_name], exp.task)

if exp.persistent_variables:
    print('\nPersistent variables ', end = '')
    pv_folder = os.path.join(data_dir, 'persistent_variables')
    set_pv = [] # Subjects whose persistant variables have been set.
    for box_n, subject_ID in exp.subjects.items():
        subject_pv_path = os.path.join(pv_folder, '{}.txt'.format(subject_ID))
        if os.path.exists(subject_pv_path):
            with open(subject_pv_path, 'r') as pv_file:
                pv_dict = eval(pv_file.read())
            for v_name, v_value in pv_dict.items():
                boxes.boxes[box_n].set_variable(v_name, v_value, exp.task)
            set_pv.append(subject_ID)
    if len(set_pv) == exp.n_subjects:
        print('set OK.')
    elif len(set_pv) == 0:
        print('not set as none found.')
    else:
        print('not found for subjects: {}'.format(set(exp.subjects.values()) - set(set_pv)))

if not os.path.exists(data_dir):
    os.mkdir(data_dir)
boxes.open_data_file(file_paths)
boxes.print_IDs() # Print state and event information to file.

input('\nHit enter to start exp. To quit at any time, hit ctrl + c.\n\n')

boxes.write_to_file('Run started at: ' + datetime.datetime.now().strftime('%H:%M:%S') + '\n\n')

boxes.run_framework()

boxes.close_data_file()

if exp.persistent_variables:
    print('\nStoring persistent variables.')
    if not os.path.exists(pv_folder):
        os.mkdir(pv_folder)
    for box_n, subject_ID in exp.subjects.items():
        pv_dict = {}
        for v_name in exp.persistent_variables:
            pv_dict[v_name] = boxes.boxes[box_n].get_variable(v_name, exp.task)
        subject_pv_path = os.path.join(pv_folder, '{}.txt'.format(subject_ID))
        with open(subject_pv_path, 'w') as pv_file:
            pv_file.write(pformat(pv_dict))

if exp.summary_data:
    try:
        import pyperclip
        print('\nCopying summary data to clipboard.')
        spacing = 1 # Number of lines between summary data lines.
        if type(exp.summary_data[-1]) == int: # Use user defined spacing.
            spacing = exp.summary_data[-1]
            exp.summary_data = exp.summary_data[:-1]
        summary_string = ''
        for v_name in exp.summary_data:
            v_values = [str(boxes.boxes[box_n].get_variable(v_name, exp.task)) + '\n'
                        for box_n in boxes_in_use]   
            v_values[0] = v_values[0].replace('\n','\t{}\n'.format(v_name.split('.')[-1]))
            v_values.append('\n' * spacing) # Add empty lines between variables.
            summary_string += ''.join(v_values) 
        pyperclip.copy(summary_string.strip()) # Copy to clipboard.
    except ImportError:
        print('Summary data not copied to clipboad as pyperclip not installed')

boxes.close()

if exp.transfer_folder: 
    transfer_folder = exp.transfer_folder
else:
    transfer_folder = cf.transfer_dir
if transfer_folder:
    print('\nCopying files to transfer folder.')
    if not os.path.exists(transfer_folder):
        os.mkdir(transfer_folder)
    for file_path in file_paths.values():
        shutil.copy2(self.file_path, transfer_folder)

input('\nHit any key to close program.')