import os
import re
import sys
from serial import SerialException

if __name__ == "__main__": # Add parent directory to path to allow imports.
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not parent_dir in sys.path: sys.path.insert(0, parent_dir)

# Catch errors importing user created config files.
try: 
    from config import config
except Exception as e:
    print('Unable to import file config.py\n')
    print(str(e))
    input('\nPress any key to close.')
    sys.exit()

from cli.pycboard import Pycboard
from cli.default_paths import data_dir, tasks_dir
from cli.pyboard import PyboardError

# ----------------------------------------------------------------------------------------
# Config menus.
# ----------------------------------------------------------------------------------------

def task_select_menu(board):
    available_tasks = {i+1: t.split('.')[0] for i, t in enumerate([ f for f in 
                       os.listdir(tasks_dir) if f[-3:] == '.py'])}
    while True:
        print('\nAvailable tasks:\n')
        for t in available_tasks.keys():
            print('{}: {}\n'.format(t, available_tasks[t]))
        i = input('Select task number, [b] for board config menu, [c] to close program:')
        if i == 'c':
            close_program(board)
        elif i == 'b':
            board_config_menu(board)
        else:
            try:
                task = available_tasks[int(i)]
                print('')
                task_menu(board, task)
            except (KeyError, ValueError):
                print('\nInput not recognised.')

def task_menu(board, task):
    try:
        board.setup_state_machine(task, raise_exception=True)
    except PyboardError:
        input('Press enter to return to task select menu.')
        return
    while True:
        i = input('\nPress [enter] to run task, [g] to get variable value, [s] to set variable value, [c] to close program or [t] to select a new task:')
        if i == '':
            print('\nRunning task, press ctrl+c to stop.\n')
            try:
                board.run_framework(verbose=True, raise_exception=True)
            except PyboardError as e:
                print('\nError while running task:\n')
                print(str(e))
                input('\nPress enter to return to task select menu.')
                return
        elif i == 'g':
            configure_variables(board, task, 'get')
        elif i == 's':
            configure_variables(board, task, 'set')
        elif i == 'c':
            close_program(board)
        elif i == 't':
            return
        else:
            print('\nInput not recognised.')


def board_config_menu(board):
    mass_storage_enabled = 'MSC' in board.status['usb_mode']
    while True:
        i = input('''\nConfig menu:
                     \n 1. Reload framwork.
                     \n 2. Reload hardware definition.
                     \n 3. Hard reset board.
                     \n 4. Reset filesystem.
                     \n 5. Enter device firmware update (DFU) mode.
                     \n 6. {} mass storage.
                     \n 7. Close program.
                     \n 8. Exit config menu.\n'''.format(
                           'Disable' if mass_storage_enabled else 'Enable'))
        try:
            selection = int(i)
        except:
            selection = None
        if selection == 1:
            board.load_framework()
        elif selection == 2:
            board.load_hardware_definition()
        elif selection == 3:
            board.hard_reset()
        elif selection == 4:
            board.reset_filesystem()
        elif selection == 5:
            board.DFU_mode()
            input('Press any key to close program.')
            board.close()
            sys.exit()
        elif selection == 6:
            if mass_storage_enabled:
                board.disable_mass_storage()
            else:
                board.enable_mass_storage()
            input('Press any key to close program.')
            sys.exit()
        elif selection == 7:
            board.close()
            sys.exit()
        elif selection == 8:
            return
        else:
            print('\nInput not recognised.')  

def configure_variables(board, task, get_or_set):
    # Get task variables by reading file.
    task_variables = []
    pattern = "v\.(?P<vname>\w+)\s*\="
    with open(os.path.join(tasks_dir, task+'.py'), "r") as file:
        file_content = file.read()
    for v_name in re.findall(pattern, file_content):
        if not v_name in [var_name for var_name in task_variables]:
            task_variables.append(v_name)
    task_variables = {i+1: v for i, v in enumerate(task_variables)}
    print('\nVariables found:\n')
    for j, v_name in task_variables.items():
        print('{}: {}\n'.format(j,v_name))
    v = input('Enter name or number of variable to {}:'.format(get_or_set))
    try:
        v_name = task_variables[int(v)]
    except:
        v_name = v
    if get_or_set == 'get':
        v_value = board.get_variable(v_name)
        if v_value is not None:
            if type(v_value) is str:
                v_value = "'{}'".format(v_value)
            print('\n{}: {}'.format(v_name, v_value))
    elif get_or_set == 'set':
        v_value = None
        while v_value is None:
            try:
                v_value = eval(input('\nEnter value for variable {}: '.format(v_name)))
            except Exception:
                print('\nUnable to interpret value.')
        if board.set_variable(v_name, v_value):
            if type(v_value) is str:
                v_value = "'{}'".format(v_value)
            print('\nVariable {} set to: {}'.format(v_name, v_value))

def close_program(board):
    board.close()
    sys.exit()

# ----------------------------------------------------------------------------------------
# Run task
# ----------------------------------------------------------------------------------------

def run_task():
    board = None
    while not board:
        i = input('Enter serial port of board or board number: ')
        try: # Check if input is an integer corresponding to a setup number.
            port = config.board_serials[int(i)]
        except:
            port = i
        try:
            board = Pycboard(port, raise_exception=True, verbose=False)
        except SerialException:
            print('\nUnable to open serial connection {}, Check serial port is correct.\n'
                  'If port is correct, try resetting pyboard with reset button.\n'.format(port))

    print('\nSerial connection OK. Micropython version: {}'.format(board.micropython_version))

    if not board.status['framework']:
        print('')
        board.load_framework()

    if not board.status['hardware']:
        print('')
        board.load_hardware_definition()

    task_select_menu(board)

if __name__ == "__main__":
    try:
        run_task()
    except Exception as e:
        print('\nError:\n')
        print(str(e))
        input('\nPress any key to close.')
    except PyboardError as e: # No need to print error message as pycboard handles it.
        print('\nPyboard error:\n')
        print(str(e))
        input('\nPress any key to close.')