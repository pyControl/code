import os
import re
import sys
from serial import SerialException

if __name__ == "__main__": # Add parent directory to path to allow imports.
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)) ) 

from cli.pycboard import Pycboard
from cli.default_paths import data_dir, tasks_dir
from cli.pyboard import PyboardError

# ----------------------------------------------------------------------------------------
# Config menus.
# ----------------------------------------------------------------------------------------

def configure_board(board):
    selection = None
    while selection != 7:
        selection = int(input('''\n\nConfig menu:
                                 \n\n 1. Reload framwork.
                                 \n\n 2. Reload hardware definition.
                                 \n\n 3. Hard reset board.
                                 \n\n 4. Reset filesystems.
                                 \n\n 5. Enter device firmware update (DFU) mode.
                                 \n\n 6. Close program.
                                 \n\n 7. Exit config menu.\n\n'''))                        
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
            board.close()
            sys.exit()  

def configure_variables(board, task):
    # Get task variables by reading file.
    task_variables = []
    pattern = "v\.(?P<vname>\w+)\s*\="
    with open(os.path.join(tasks_dir, task+'.py'), "r") as file:
        file_content = file.read()
    for v_name in re.findall(pattern, file_content):
        if not v_name in [var_name for var_name in task_variables]:
            task_variables.append(v_name)
    task_variables = {i+1: v for i, v in enumerate(task_variables)}
    while True:
        i = input('\nEnter [g] to get variables value, [s] to set variables value, [x] to exit menu:')
        if i == 'x': break
        if i in ['g','s']:
            print('\nVariables found:\n')
            for j, v_name in task_variables.items():
                print('{}: {}\n'.format(j,v_name))
            v = input('Enter variable number or variable name:')
            try:
                v_name = task_variables[int(v)]
            except:
                v_name = v
            if i == 'g':
                v_value = board.get_variable(v_name)
                if v_value is not None:
                    print('\n{}: {}'.format(v_name, v_value))
            elif i == 's':
                v_value = eval(input('\nEnter variable value: '))
                set_OK = board.set_variable(v_name, v_value)
                if set_OK:
                    print('\nVariable {} set to: {}'.format(v_name, v_value))

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
            print('\nUnable to open serial connection, Check serial port is correct.\n' 
                  'If port is correct, try resetting pyboard with reset button.\n')

    if not board.status['framework']:
        print('\nFramework not loaded, uploading framework..')
        board.load_framework()

    if not board.status['hardware']:
        print('\nHardware definition not loaded, uploading hardware definition..')
        board.load_hardware_definition()

    available_tasks = {i+1: t.split('.')[0] for i, t in enumerate([ f for f in 
                       os.listdir(tasks_dir) if f[-3:] == '.py'])}

    task_n = None
    while task_n not in available_tasks.keys():
        print('\nAvailable tasks:\n')
        for i in available_tasks.keys():
            print('{}: {}\n'.format(i, available_tasks[i]))
        task_n = int(input('Select task number, or [0] for board config menu:'))
        if task_n == 0: 
            configure_board(board)
        else:
            task = available_tasks[task_n]
            print('')

    board.setup_state_machine(task, raise_exception=True)

    i = None
    while i is not 'c':
        i = input('\nPress [enter] to run task, [v] to configure variables, or [c] to close program:')
        if i == '':
            print('\nRunning task, press ctrl+c to stop.\n')
            board.run_framework(verbose=True)
        elif i == 'v':
            configure_variables(board, task)

    board.close()

if __name__ == "__main__":
    try:
        run_task()
    except Exception as e:
        print('\nError:\n')
        print(str(e))
        input('\nPress any key to close.')
    except PyboardError: # No need to print error message as pycboard handles it.
        pass
        input('\nPress any key to close.')