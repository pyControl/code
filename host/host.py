import kick
import pyboard as pb
import os
import time

# ----------------------------------------------------------------------------------------
# Units.
# ----------------------------------------------------------------------------------------

minute = 60000
second = 1000
ms = 1

# ----------------------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------------------

pyControl_dir = '..\\pyControl' # Path to folder of micropython pyControl framwork files.

tasks_dir = '..\\examples'

#port = 'COM23'
#board = pb.Pyboard(port)
#board.enter_raw_repl()

# ----------------------------------------------------------------------------------------
# File transfer
# ----------------------------------------------------------------------------------------

def transfer_file(board, file_path, target_path = None):
    '''Copy a file into the root directory of the pyboard.'''
    if not target_path:
        target_path = os.path.split(file_path)[-1]
    data = open(file_path).read()
    board.exec("tmpfile = open('{}','w')".format(target_path))
    board.exec("tmpfile.write({data})".format(data=repr(data)))
    board.exec('tmpfile.close()')

def transfer_folder(board, folder_path, target_folder = None, file_type = 'all'):
    '''Copy a folder into the root directory of the pyboard.  Folders that
    contain subfolders will not be copied successfully.  To copy only files of
    a specific type, change the file_type argument to the file suffix (e.g. 'py').'''
    if not target_folder:
        target_folder = os.path.split(folder_path)[-1]
    files = os.listdir(folder_path)
    if file_type != 'all':
        files = [f for f in files if f.split('.')[-1] == file_type]
    try:
        board.exec('import os;os.mkdir({})'.format(repr(target_folder)))
    except pb.PyboardError:
        pass # Folder already exists.
    for f in files:
        file_path = os.path.join(folder_path, f)
        target_path = target_folder + '/' + f
        transfer_file(board, file_path, target_path)

def load_framework(board):
    'Load the pyControl framework folder to the specified board.'
    transfer_folder(board, pyControl_dir, file_type = 'py')

# ----------------------------------------------------------------------------------------
# pyControl operations.
# ----------------------------------------------------------------------------------------

def board_reset(board):
    board.enter_raw_repl()
    board.exec('from pyControl import *;import os')


def setup_state_machine(board, sm_name, hardware = None, sm_dir = None):
    ''' Transfer state machine descriptor file sm_name.py from
    folder sm_dir (defaults to tasks_dir) to board. Instantiate
    state machine object as sm_name_instance. Hardware obects can be instantiated
    and passed to the state machine constructor by setting the hardware argument to
    a string which instantiates a hardware object. 
    '''
    if not sm_dir:
        sm_dir = tasks_dir
    sm_path = os.path.join(sm_dir, sm_name + '.py')
    assert os.path.exists(sm_path), 'State machine file not found at: ' + sm_path
    transfer_file(board, sm_path)
    board.exec('import {}'.format(sm_name)) 
    board.exec('os.remove({})'.format(repr(sm_name + '.py')))
    if hardware:
        board.exec('hwo = ' + hardware) # Instantiate a hardware object.
    else:
        board.exec('hwo = None')
    board.exec(sm_name + '_instance = sm.State_machine({}, hwo)'.format(sm_name))


def run_framework(board, dur, verbose = False):
    '''Run framework for specified duration (seconds), printing output to '''
    board.exec('fw.verbose = ' + repr(verbose))
    start_time = time.time()
    board.exec_raw_no_follow('fw.run({})'.format(dur))
    data = board.serial.read(1)
    while True:
        if data.endswith(b'\x04'): # End of framework run.
            break
        elif data.endswith(b'\r\n'):  # End of data line.
            print(data[:-1].decode()) 
            data = board.serial.read(1)
        elif board.serial.inWaiting() > 0:
            new_data = board.serial.read(1)
            data = data + new_data
    data_err = board.read_until(2, b'\x04>', timeout=10) # If not included, micropython board appears to crash/reset.


def run_state_machine(board, sm_name, dur, hardware = None, sm_dir = None,
                      verbose = False):
    '''Run the state machine sm_name from directory sm_dir on the specified 
    board for the specified duration. 
    Usage examples:
        host.run_state_machine(board, 'blinker', 5) 
        host.run_state_machine(board, 'two_step', 20, 'hw.Box()', verbose = True)
    '''
    board_reset(board)
    setup_state_machine(board, sm_name, hardware, sm_dir)
    run_framework(board, dur, verbose)

