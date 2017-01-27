import os
import sys
import datetime
from pprint import pformat
import shutil
from imp import reload

if __name__ == "__main__": # Add parent directory to path to allow imports.
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)) ) 

from cli.pycboard import Pycboard
from cli.default_paths import data_dir, tasks_dir

# ----------------------------------------------------------------------------------------
# Config menu.
# ----------------------------------------------------------------------------------------

def config_menu(board):
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
            board.load_framework()
        elif selection == 2:
            board.load_hardware_definition()
        elif selection == 3:
            board.save_unique_IDs()
        elif selection == 4:
            board.hard_reset()
        elif selection == 5:
            board.reset_filesystem()
        elif selection == 6:
            board.close()
            sys.exit()

# ----------------------------------------------------------------------------------------
# Run experiment
# ----------------------------------------------------------------------------------------



def run_task():
    board = None
    while not board:
        try:
            port = input('Enter serial port of board: ')
            board = Pycboard(port, raise_exception=True, verbose=False)
        except SerialException:
            print('Unable to open serial connection, Check serial port entered is correct.\n' 
                  'If port is correct, try resetting pyboard with reset button.')

    if not board.status['framework']:
        print('Framework not loaded, uploading framework..')
        board.load_framework()

    if not board.status['hardware']:
        print('Hardware definition not loaded, uploading hardware definition..')
        board.load_hardware_definition()


    available_tasks = {i+1: t.split('.')[0] for i, t in enumerate([ f for f in 
                       os.listdir(tasks_dir) if f[-3:] == '.py'])}

    task_n = -1
    while task_n not in available_tasks.keys():
        print('Available tasks:\n')
        for i in available_tasks.keys():
            print('{}: {}\n'.format(i, available_tasks[i]))
        task_n = int(input('Select task number to upload, or 0 for config menu:'))
        if task_n == 0: 
            config_menu(board)

    board.setup_state_machine(available_tasks[task_n])

    input('\nHit enter to run task. To stop task press ctrl + c.\n\n')

    board.run_framework(verbose=True)

    board.close()

if __name__ == "__main__":
    try:
        run_task()
    except Exception as e:
        #if board: board.close()
        print('\nError:\n')
        print(str(e))
        input('\nUnable to run experiment, press any key to close.')