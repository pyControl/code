import kick
from pyboard import Pyboard, PyboardError
import os
import time

# ----------------------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------------------

pyControl_dir = os.path.join('..', 'pyControl') # Path to folder of pyControl framwork files.

examples_dir = os.path.join('..', 'examples') # Path to folder of example scripts.

# ----------------------------------------------------------------------------------------
#  Pycboard class.
# ----------------------------------------------------------------------------------------

class Pycboard(Pyboard):
    '''Pycontrol board instance inherits functionally from Pyboard and adds functionallity
    for file transfer and pyControl operations.
    '''

    def __init__(self, serial_device, baudrate=115200):
        super().__init__(serial_device, baudrate=115200)
        try:
            self.reset() 
        except PyboardError:
            self.load_framework()
            self.reset()
                             
    # ------------------------------------------------------------------------------------
    # File transfer
    # ------------------------------------------------------------------------------------

    def transfer_file(self, file_path, target_path = None):
        '''Copy a file into the root directory of the pyboard.'''
        if not target_path:
            target_path = os.path.split(file_path)[-1]
        data = open(file_path).read()
        self.exec("tmpfile = open('{}','w')".format(target_path))
        self.exec("tmpfile.write({data})".format(data=repr(data)))
        self.exec('tmpfile.close()')


    def transfer_folder(self, folder_path, target_folder = None, file_type = 'all'):
        '''Copy a folder into the root directory of the pyboard.  Folders that
        contain subfolders will not be copied successfully.  To copy only files of
        a specific type, change the file_type argument to the file suffix (e.g. 'py').'''
        if not target_folder:
            target_folder = os.path.split(folder_path)[-1]
        files = os.listdir(folder_path)
        if file_type != 'all':
            files = [f for f in files if f.split('.')[-1] == file_type]
        try:
            self.exec('import os;os.mkdir({})'.format(repr(target_folder)))
        except PyboardError:
            pass # Folder already exists.
        for f in files:
            file_path = os.path.join(folder_path, f)
            target_path = target_folder + '/' + f
            self.transfer_file(file_path, target_path)

    def load_framework(self):
        'Copy the pyControl framework folder to the board.'
        print('Transfering pyControl framework to pyboard.')
        self.transfer_folder(pyControl_dir, file_type = 'py')

    def remove_file(self, file_path):
        'Remove a file from the pyboard.'
        self.exec('os.remove({})'.format(repr(file_path)))

    # ------------------------------------------------------------------------------------
    # pyControl operations.
    # ------------------------------------------------------------------------------------

    def reset(self):
        'Enter raw repl (soft reboots pyboard), import modules.'
        self.enter_raw_repl()
        self.exec('from pyControl import *;import os')


    def setup_state_machine(self, sm_name, hardware = None, sm_dir = None):
        ''' Transfer state machine descriptor file sm_name.py from folder sm_dir
        (defaults to examples_dir) to board. Instantiate state machine object as 
        sm_name_instance. Hardware obects can be instantiated and passed to the 
        state machine constructor by setting the hardware argument to a string which
        instantiates a hardware object. 
        '''
        if not sm_dir:
            sm_dir = examples_dir
        sm_path = os.path.join(sm_dir, sm_name + '.py')
        assert os.path.exists(sm_path), 'State machine file not found at: ' + sm_path
        print('Transfering state machine {} to pyboard.'.format(repr(sm_name)))
        self.transfer_file(sm_path)
        self.exec('import {}'.format(sm_name)) 
        self.remove_file(sm_name + '.py')
        if hardware:
            self.exec('hwo = ' + hardware) # Instantiate a hardware object.
        else:
            self.exec('hwo = None')
        self.exec(sm_name + '_instance = sm.State_machine({}, hwo)'.format(sm_name))


    def run_framework(self, dur, verbose = False):
        '''Run framework for specified duration (seconds).'''
        self.exec('fw.verbose = ' + repr(verbose))
        self.exec_raw_no_follow('fw.run({})'.format(dur))
        data = self.serial.read(1)
        while True:
            if data.endswith(b'\x04'): # End of framework run.
                break
            elif data.endswith(b'\r\n'):  # End of data line.
                print(data[:-1].decode()) 
                data = self.serial.read(1)
            elif self.serial.inWaiting() > 0:
                new_data = self.serial.read(1)
                data = data + new_data
        data_err = self.read_until(2, b'\x04>', timeout=10) # If not included, micropython board appears to crash/reset.


    def run_state_machine(self, sm_name, dur, hardware = None, sm_dir = None,
                          verbose = False):
        '''Run the state machine sm_name from directory sm_dir for the specified 
        duration (seconds). Usage examples:
            board.run_state_machine('blinker', 5) 
            board.run_state_machine('two_step', 20, 'hw.Box()', verbose = True)
        '''
        self.reset()
        self.setup_state_machine(sm_name, hardware, sm_dir)
        self.run_framework(dur, verbose)
