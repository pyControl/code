from config import experiments
from config import config
from .experiment import Experiment
from .pycboards import Pycboards
import datetime
from pprint import pformat
from sys import exit
import shutil
import os
from imp import reload

# ----------------------------------------------------------------------------------------
# Config menu.
# ----------------------------------------------------------------------------------------

def config_menu():
    print('\n\nOpening connection to all boards listed in config.py.\n\n')
    boards = Pycboards(config.board_serials.keys())
    selection = None
    while selection != 7:
        selection = int(input('''\n\nConfig menu:
                                 \n\n 1. Reload framwork.
                                 \n\n 2. Reload hardware definition.
                                 \n\n 3. Save hardware IDs.
                                 \n\n 4. Hard reset boards.
                                 \n\n 5. Reset filesystems.
                                 \n\n 6. Close program.
                                 \n\n 7. Exit config menu.\n\n'''))
                                 
        if selection == 1:
            boards.load_framework()
        elif selection == 2:
            boards.load_hardware_definition()
        elif selection == 3:
            boards.save_unique_IDs()
        elif selection == 4:
            boards.hard_reset()
        elif selection == 5:
            boards.reset_filesystem()
        elif selection == 6:
            boards.close()
            exit()
    boards.close()

# ----------------------------------------------------------------------------------------
# Run experiment
# ----------------------------------------------------------------------------------------

def run_experiment():
    reload(experiments)
    reload(config)

    # Create list of available experiments

    if hasattr(experiments,'experiments'):
        exp_list = experiments.experiments # List of experiments specified in experiments.py
    else:
        exp_list = [e for e in [getattr(experiments, c) for c in dir(experiments)]
                       if isinstance(e, Experiment)] # Construct list of available experiments.

    date = datetime.date.today().strftime('-%Y-%m-%d')

    selection = 0
    while selection == 0: 

        print('\nExperiments available:\n')

        for i, exp in enumerate(exp_list):
          print('\nExperiment number : {}  Name:  {}\n'.format(i + 1, exp.name))
          for board_n, subject_ID in exp.subjects.items():
            print('    Box : {}   {}'.format(board_n, subject_ID))

        selection = int(input('\n\nEnter number of experiment to run, for config options enter 0: '))
        if selection == 0:
            config_menu()

    exp = exp_list[selection - 1] # The selected experiment.

    boards_in_use = sorted(list(exp.subjects.keys()))
    data_dir     = os.path.join(config.data_dir, exp.folder)
    file_paths   = {board_n: os.path.join(data_dir, exp.subjects[board_n] + date + '.txt')
                           for board_n in boards_in_use}

    print('')

    boards = Pycboards(boards_in_use)

    if not boards.check_unique_IDs():
        input('Hardware ID check failed, press any key to close program.')
        boards.close()
        exit()

    if input('\nRun hardware test? (y / n) ') == 'y':
        print('\nUploading hardware test.\n')
        boards.setup_state_machine(config.hardware_test)
        if config.hardware_test_display_output:
            print('\nPress CTRL + C when finished with hardware test.\n')
            boards.run_framework()
        else: 
            boards.start_framework(data_output = False)
            input('\nPress any key when finished with hardware test.')
            boards.stop_framework()
    else:
        print('\nSkipping hardware test.')

    print('\nUploading task.\n')

    boards.setup_state_machine(exp.task)

    if exp.set_variables: # Set state machine variables from experiment specification.
        print('\nSetting state machine variables.')
        for v_name in exp.set_variables:
            boards.set_variable(v_name, exp.set_variables[v_name], exp.task)

    if exp.persistent_variables:
        print('\nPersistent variables ', end = '')
        pv_folder = os.path.join(data_dir, 'persistent_variables')
        set_pv = [] # Subjects whose persistant variables have been set.
        for board_n, subject_ID in exp.subjects.items():
            subject_pv_path = os.path.join(pv_folder, '{}.txt'.format(subject_ID))
            if os.path.exists(subject_pv_path):
                with open(subject_pv_path, 'r') as pv_file:
                    pv_dict = eval(pv_file.read())
                for v_name, v_value in pv_dict.items():
                    boards.boards[board_n].set_variable(v_name, v_value, exp.task)
                set_pv.append(subject_ID)
        if len(set_pv) == exp.n_subjects:
            print('set OK.')
        elif len(set_pv) == 0:
            print('not set as none found.')
        else:
            print('not found for subjects: {}'.format(set(exp.subjects.values()) - set(set_pv)))

    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    boards.open_data_file(file_paths)
    boards.print_IDs() # Print state and event information to file.

    input('\nHit enter to start exp. To quit at any time, hit ctrl + c.\n\n')

    boards.write_to_file('\nI Run started at: ' + datetime.datetime.now().strftime('%H:%M:%S') + '\n\n')

    boards.run_framework()

    boards.close_data_file()

    if exp.persistent_variables:
        print('\nStoring persistent variables.')
        if not os.path.exists(pv_folder):
            os.mkdir(pv_folder)
        for board_n, subject_ID in exp.subjects.items():
            pv_dict = {}
            for v_name in exp.persistent_variables:
                pv_dict[v_name] = boards.boards[board_n].get_variable(v_name, exp.task)
            subject_pv_path = os.path.join(pv_folder, '{}.txt'.format(subject_ID))
            with open(subject_pv_path, 'w') as pv_file:
                pv_file.write(pformat(pv_dict))

    if exp.summary_data:
        try:
            import pyperclip
            spacing = 1 # Number of lines between summary data lines.
            if type(exp.summary_data[-1]) == int: # Use user defined spacing.
                spacing = exp.summary_data[-1]
                exp.summary_data = exp.summary_data[:-1]
            summary_string = ''
            for v_name in exp.summary_data:
                v_values = [str(boards.boards[board_n].get_variable(v_name, exp.task)) + '\n'
                            for board_n in boards_in_use]   
                v_values[0] = v_values[0].replace('\n','\t{}\n'.format(v_name.split('.')[-1]))
                v_values.append('\n' * spacing) # Add empty lines between variables.
                summary_string += ''.join(v_values) 
            boards.close()
            input('\nPress any key to copy summary data to clipboard.')
            pyperclip.copy(summary_string.strip()) # Copy to clipboard.
        except ImportError:
            print('Summary data not copied to clipboad as pyperclip not installed')
    else:
        boards.close()

    if exp.transfer_folder: 
        transfer_folder = exp.transfer_folder
    else:
        transfer_folder = config.transfer_dir
    if transfer_folder:
        print('\nCopying files to transfer folder.')
        if not os.path.exists(transfer_folder):
            os.mkdir(transfer_folder)
        for file_path in file_paths.values():
            shutil.copy2(file_path, transfer_folder)

    input('\nHit any key to close program.')