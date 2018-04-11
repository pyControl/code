import os
import sys
import time
from serial import SerialException
from serial.tools import list_ports

# Add parent directory to path to allow imports.
top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not top_dir in sys.path: sys.path.insert(0, top_dir)

from com.pycboard import Pycboard, PyboardError
from com.data_logger import Data_logger
from config.paths import data_dir, tasks_dir

# Catch errors importing user created config files.
try: 
    from config import config
except Exception as e:
    print('Unable to import file config.py\n')
    print(str(e))
    input('\nPress any key to close.')
    sys.exit()

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
            task = None
            try:
                task = available_tasks[int(i)]
            except (KeyError, ValueError):
                print('\nInput not recognised.')
            if task:
                task_menu(board, task)

def task_menu(board, task):
    try:
        sm_info = board.setup_state_machine(task, raise_exception=True)
        data_logger = Data_logger(data_dir, 'run_task', task, sm_info)
    except Exception as e:
        print(e)
        input('Press enter to return to task select menu.')
        return
    subject_ID = None
    while True:
        i = input('\n\nPress [enter] to run task, [g] to get variable value, [s] to set variable value, [c] to close program, [f] to create data file, or [t] to select a new task:')
        if i == '':
            if subject_ID: 
                data_logger.open_data_file(subject_ID)
            else:
                r = input('\nData file not created, data will not be saved. Continue ([y]/n)')
                if r == 'n':
                    continue
            print('\nRunning task, press ctrl+c to stop.\n')
            try:
                board.start_framework()
                while True:
                    new_data = board.process_data()
                    print(data_logger.data_to_string(new_data, verbose=True), end='')
                    if subject_ID: data_logger.write_to_file(new_data)
            except KeyboardInterrupt:
                board.stop_framework()
                time.sleep(0.1)
                new_data = board.process_data()
                print(data_logger.data_to_string(new_data, verbose=True), end='')
                if subject_ID: data_logger.write_to_file(new_data)
            except PyboardError as e:
                print('\nError while running task:\n')
                print(str(e))
            if subject_ID:
                data_logger.close_files()
            input('\nPress enter to return to task select menu.')
            return
        elif i == 'g':
            configure_variables(board, 'get')
        elif i == 's':
            configure_variables(board, 'set')
        elif i == 'c':
            close_program(board)
        elif i == 'f':
            subject_ID = input('\nCreating data file, enter subject_ID:')
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

def configure_variables(board, get_or_set):
    # Get task variables by reading file.
    task_variables = {i+1: v for i, v in enumerate(board.sm_info['variables'])}
    print('\nVariables:')
    for i, v_name in task_variables.items():
        print('{}: {}\n'.format(i,v_name))
    v_name = None
    while v_name == None:
        v = input('\nEnter name or number of variable to {}:'.format(get_or_set))
        try:
            v_name = task_variables[int(v)]
        except (ValueError, KeyError):
            if v in task_variables.values():
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
                print('\nInvalid value.')
        board.set_variable(v_name, v_value)
        if type(v_value) is str: v_value = "'{}'".format(v_value)
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
        i = input('Enter serial port of board or board number, or [s] to scan for pyboards: ')
        if i == 's':
            pyboard_serials = {j+1: b for (j,b) in 
                enumerate([c[0] for c in list_ports.comports() if 'Pyboard' in c[1]])}
            unknown_usb_serials = {j+len(pyboard_serials)+1: b for (j,b) in 
                enumerate([c[0] for c in list_ports.comports() if 'USB Serial Device' in c[1]])}
            if not (pyboard_serials or unknown_usb_serials):
                print('\nNo Pyboards found.\n' )
                continue
            else:
                if pyboard_serials:
                    print('\nPyboards found on the following serial ports:\n')
                    for b in pyboard_serials.keys():
                        print('{}: {}\n'.format(b, pyboard_serials[b]))
                if unknown_usb_serials:
                    print('\nPossible Pyboards found on the following serial ports:\n')
                    for b in unknown_usb_serials.keys():
                        print('{}: {}\n'.format(b, unknown_usb_serials[b]))
                pyboard_serials.update(unknown_usb_serials)
                while True:
                    k = input('Select Pyboard:')
                    try:
                        port = pyboard_serials[int(k)]
                        break
                    except (KeyError, ValueError):
                        print('\nInput not recognised, valid inputs: {}\n'.format(list(pyboard_serials.keys())))
        else:
            try: # Check if input is an integer corresponding to a setup number.
                port = config.board_serials[int(i)]
            except (KeyError, ValueError):
                port = i
        try:
            board = Pycboard(port, raise_exception=True, verbose=False)
        except SerialException:
            print('\nUnable to open serial connection {}, Check serial port is correct.\n'
                  'If port is correct, try resetting pyboard with reset button.\n'.format(port))

    print('\nSerial connection OK. Micropython version: {}'.format(board.micropython_version))

    if not board.status['framework']:
        board.load_framework()

    if not board.status['hardware']:
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