import os
import sys
from datetime import datetime
from pprint import pformat
import shutil
from imp import reload

# Add parent directory to path to allow imports.
top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not top_dir in sys.path: sys.path.insert(0, top_dir)

from cli.experiment import Experiment
from com.pycboards import Pycboards
from config.paths import data_dir, tasks_dir, transfer_dir

# Catch errors importing user created config files.
try: 
    from config import config
except Exception as e:
    print('Unable to import file config.py\n')
    print(str(e))
    input('\nPress any key to close.')
    sys.exit()

try: 
    from config import experiments
except Exception as e:
    print('Unable to import file experiments.py\n')
    print(str(e))
    input('\nPress any key to close.')
    sys.exit()

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
            sys.exit()
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

    selection = 0
    while selection == 0: 

        print('\nExperiments available:\n')

        for i, exp in enumerate(exp_list):
          print('\nExperiment number : {}  Name:  {}\n'.format(i + 1, exp.name))
          for n, subject_ID in exp.subjects.items():
            print('    Box : {}   {}'.format(n, subject_ID))

        selection = int(input('\n\nEnter number of experiment to run, for config options enter 0: '))
        if selection == 0:
            config_menu()

    exp = exp_list[selection - 1] # The selected experiment.

    if not os.path.exists(os.path.join(tasks_dir, exp.task + '.py')):
        print('\nError: State machine file {} not found.'.format(exp.task))
        input('\nPress any key to close program.')
        sys.exit()

    boards_in_use = sorted(list(exp.subjects.keys()))
    exp_dir     = os.path.join(data_dir, exp.folder)

    print('')

    boards = Pycboards(boards_in_use)

    if not boards.check_unique_IDs():
        input('Hardware ID check failed, press any key to close program.')
        boards.close()
        sys.exit()

    if input('\nRun hardware test? (y/[n]) ') == 'y':
        print('\nUploading hardware test.')
        boards.setup_state_machine(config.hardware_test)
        if config.hardware_test_display_output:
            print('\nPress CTRL + C when finished with hardware test.\n')
            boards.run_framework()
        else: 
            boards.start_framework(data_output=False)
            input('\nPress any key when finished with hardware test.')
            boards.stop_framework()
    else:
        print('\nSkipping hardware test.')

    print('\nUploading task.')

    boards.setup_state_machine(exp.task)

    if exp.set_variables: # Set state machine variables from experiment specification.
        print('\nSetting state machine variables.')
        for v_name in exp.set_variables:
            boards.set_variable(v_name, exp.set_variables[v_name])

    if exp.persistent_variables:
        print('\nPersistent variables ', end = '')
        pv_folder = os.path.join(exp_dir, 'persistent_variables')
        set_pv = [] # Subjects whose persistant variables have been set.
        for n, subject_ID in exp.subjects.items():
            subject_pv_path = os.path.join(pv_folder, '{}.txt'.format(subject_ID))
            if os.path.exists(subject_pv_path):
                with open(subject_pv_path, 'r') as pv_file:
                    pv_dict = eval(pv_file.read())
                for v_name, v_value in pv_dict.items():
                    boards.boards[n].set_variable(v_name, v_value)
                set_pv.append(subject_ID)
        if len(set_pv) == exp.n_subjects:
            print('set OK.')
        elif len(set_pv) == 0:
            print('not set as none found.')
        else:
            print('not found for subjects: {}'.format(set(exp.subjects.values()) - set(set_pv)))

    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    if not os.path.exists(exp_dir):
        os.mkdir(exp_dir)

    input('\nHit enter to start exp. To stop experiment when running, hit ctrl + c.\n')

    boards.open_data_file(exp_dir, exp.name, exp.subjects, datetime.now())
    file_paths = boards.get_file_paths()

    boards.run_framework()

    if exp.persistent_variables:
        print('\nStoring persistent variables.')
        if not os.path.exists(pv_folder):
            os.mkdir(pv_folder)
        for n, subject_ID in exp.subjects.items():
            pv_dict = {}
            for v_name in exp.persistent_variables:
                pv_dict[v_name] = boards.boards[n].get_variable(v_name)
            subject_pv_path = os.path.join(pv_folder, '{}.txt'.format(subject_ID))
            with open(subject_pv_path, 'w') as pv_file:
                pv_file.write(pformat(pv_dict))

    if exp.summary_variables:        
        spacing = exp.summary_variables.pop() if isinstance(exp.summary_variables[-1], int) else 1
        if spacing < 1: spacing = 1
        summary_string = ''
        print('\nSummary variables:')
        for v_name in exp.summary_variables:
            print('\n' + v_name + ':')
            v_strings = [v_name + ':\n']
            for n in boards_in_use:
                v_value = boards.boards[n].get_variable(v_name)
                boards.boards[n].data_logger.data_file.write('V -1 {} {}\n'.format(v_name, v_value))
                print(exp.subjects[n] + ': {}'.format(v_value))
                v_strings.append(str(v_value) +'\t' + exp.subjects[n] + '\n')
            v_strings.append('\n' * (spacing-1)) # Add empty lines between variables.
            summary_string += ''.join(v_strings) 
        try:
            import pyperclip
            pyperclip.copy(summary_string.strip()) # Copy to clipboard.
            print('\nSummary data copied to clipboad.')
        except ImportError:
            print('\nSummary data not copied to clipboad as pyperclip not installed.')


    boards.close_data_file()
    boards.close()

    if transfer_dir:
        transfer_folder = os.path.join(config.transfer_dir, exp.folder)
        print('\nCopying files to transfer folder.')
        if not os.path.exists(transfer_folder):
            os.mkdir(transfer_folder)
        for file_path in file_paths.values():
            shutil.copy2(file_path, transfer_folder)

    if len(boards.board_errors):
        print('\nWarning:  Errors occured on boards {}, please check data files for traceback.'.format(boards.board_errors))

    input('\nHit any key to close program.')

if __name__ == "__main__":
    try:
        run_experiment()
    except BaseException as e:
        print('\nError:\n')
        print(str(e))
        input('\nUnable to run experiment, press any key to close.')