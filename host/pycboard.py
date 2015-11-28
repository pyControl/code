from pyboard import Pyboard, PyboardError
from config.config import *
import os
import shutil
import time
from copy import deepcopy

# ----------------------------------------------------------------------------------------
#  Pycboard class.
# ----------------------------------------------------------------------------------------

class Pycboard(Pyboard):
    '''Pycontrol board inherits from Pyboard and adds functionallity for file transfer
    and pyControl operations.
    '''

    def __init__(self, serial_device, ID_number = None, baudrate=115200):
        super().__init__(serial_device, baudrate=115200)
        try:
            self.reset() 
        except PyboardError:
            self.load_framework()
            self.reset()
        self.unique_ID = eval(self.eval('pyb.unique_id()').decode())
        self.data_file = None
        self.ID_number = ID_number

    def reset(self):
        'Enter raw repl (soft reboots pyboard), import modules.'
        self.enter_raw_repl()
        self.exec('from pyControl import *;import os')
        self.framework_running = False
        self.data = None

    # ------------------------------------------------------------------------------------
    # File transfer
    # ------------------------------------------------------------------------------------


    def write_file(self, target_path, data):
        '''Write data to file at specified path on pyboard, any data already
        in the file will be deleted.
        '''
        self.exec("tmpfile = open('{}','w')".format(target_path))
        self.exec("tmpfile.write({data})".format(data=repr(data)))
        self.exec('tmpfile.close()')


    def transfer_file(self, file_path, target_path = None):
        '''Copy a file into the root directory of the pyboard.'''
        if not target_path:
            target_path = os.path.split(file_path)[-1]
        transfer_file = open(file_path) 
        self.write_file(target_path, transfer_file.read())
        transfer_file.close()


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


    def load_hardware_definition(self, hwd_name = 'hardware_definition', hwd_dir = config_dir):
        '''Transfer a hardware definition file to pyboard.  Defaults to transfering file
        hardware_definition.py from config folder.  If annother file is specified, that
        file is transferred and given name hardware_definition.py in pyboard filesystem.'''
        hwd_path = os.path.join(hwd_dir, hwd_name + '.py')
        if os.path.exists(hwd_path):
            print('Transfering hardware definition to pyboard.')
            self.transfer_file(hwd_path, target_path = 'hardware_definition.py')
        else:
            print('Hardware definition file ' + hwd_name + '.py not found.')    

    def remove_file(self, file_path):
        'Remove a file from the pyboard.'
        self.exec('os.remove({})'.format(repr(file_path)))

    # ------------------------------------------------------------------------------------
    # pyControl operations.
    # ------------------------------------------------------------------------------------

    def setup_state_machine(self, sm_name, sm_dir = None):
        ''' Transfer state machine descriptor file sm_name.py from folder sm_dir
        (defaults to tasks_dir then examples_dir) to board. Instantiate state machine object as 
        sm_name_instance.'''
        self.reset()
        if not sm_dir:
            if os.path.exists(os.path.join(tasks_dir, sm_name + '.py')):
                sm_dir = tasks_dir
            else:
                sm_dir = examples_dir
        sm_path = os.path.join(sm_dir, sm_name + '.py')
        assert os.path.exists(sm_path), 'State machine file not found at: ' + sm_path
        print('Transfering state machine {} to pyboard.'.format(repr(sm_name)))
        self.transfer_file(sm_path)
        self.exec('import {}'.format(sm_name)) 
        self.remove_file(sm_name + '.py')
        self.exec(sm_name + '_instance = sm.State_machine({})'.format(sm_name))

    def print_IDs(self):
        'Print state and event IDs.'
        ID_info = self.exec('fw.print_IDs()').decode()
        if self.data_file: # Print IDs to file.
            self.data_file.write(ID_info)
        else: # Print to screen.
            print(ID_info)

    def start_framework(self, dur = None, verbose = False, data_output = True):
        'Start pyControl framwork running on pyboard.'
        self.exec('fw.verbose = ' + repr(verbose))
        self.exec('fw.data_output = ' + repr(data_output))
        self.exec_raw_no_follow('fw.run({})'.format(dur))
        self.framework_running = True
        self.data = b''

    def stop_framework(self):
        'Stop framework running on pyboard by sending stop command.'
        self.serial.write(b'E')
        self.framework_running = False
        data_err = self.read_until(2, b'\x04>', timeout=10) 

    def process_data(self):
        'Process data output from the pyboard to the serial line.'
        while self.serial.inWaiting() > 0:
            self.data = self.data + self.serial.read(1)  
            if self.data.endswith(b'\x04'): # End of framework run.
                self.framework_running = False
                data_err = self.read_until(2, b'\x04>', timeout=10) 
                print(data_err)
                break
            elif self.data.endswith(b'\n'):  # End of data line.
                data_string = self.data.decode() 
                if self.ID_number:
                    print('Box {}: '.format(self.ID_number), end = '')
                print(data_string[:-1]) 
                if self.data_file:
                    if data_string.split(' ')[1][0] != '#': # Output not a coment, write to file.
                        self.data_file.write(data_string)
                        self.data_file.flush()
                self.data = b''

    def run_framework(self, dur = None, verbose = False):
        '''Run framework for specified duration (seconds).'''
        self.start_framework(dur, verbose)
        try:
            while self.framework_running:
                self.process_data()     
        except KeyboardInterrupt:
            self.stop_framework()

    def run_state_machine(self, sm_name, dur, sm_dir = None, verbose = False):
        '''Run the state machine sm_name from directory sm_dir for the specified 
        duration (seconds).
        '''
        self.setup_state_machine(sm_name, sm_dir)
        self.run_framework(dur, verbose)

    # ------------------------------------------------------------------------------------
    # Getting and setting variables.
    # ------------------------------------------------------------------------------------


    def set_variable(self, sm_name, v_name, v_value, verbose = False):
        '''Set state machine variable when framework not running, some checking is 
        performed to verify variable has not got corrupted during setting.'''
        try:
            eval(repr(v_value))
        except:
            print('Set variable error, unable to eval(repr(v_value)).')
            return
        if self._check_variable_exits(sm_name, v_name):
            attempt_n, prev_set_value = (0, None)
            while attempt_n < 5:
                attempt_n += 1
                try:
                    self.exec(sm_name + '_instance.smd.v.' + v_name + '=' + repr(v_value))
                    set_value = self.get_variable(sm_name, v_name, pre_checked = True)
                    if set_value == v_value: 
                        return # Variable set exactly.
                    elif ((type(set_value) == float) and 
                          ((abs(set_value - v_value) / v_value) < 0.01)):
                        return # Variable set within floating point accuracy.
                    elif (set_value is not None) and (prev_set_value == set_value):  
                        return # Variable set consistently twice.
                    prev_set_value = deepcopy(set_value)  
                except PyboardError as e:
                    print(e) 
            print('Unable to set variable: ' + v_name)


    def get_variable(self, sm_name, v_name, pre_checked = False):
        'Get value of state machine variable when framework not running.'
        if pre_checked or self._check_variable_exits(sm_name, v_name):
            attempt_n, v_string, v_value = (0, None, None)
            while attempt_n < 5:
                attempt_n += 1
                try:
                    self.serial.flushInput()
                    v_string = self.eval(sm_name + '_instance.smd.v.' + v_name).decode()
                except PyboardError as e:
                    print(e) 
                if v_string is not None:
                    try:
                        v_value = eval(v_string)
                        if v_value is not None:
                            return v_value
                    except:
                        if attempt_n == 5:
                            print('Get variable error; unable to eval string: ' + v_string)
            print('Unable to get variable: ' + v_name)

    def _check_variable_exits(self, sm_name, v_name):
        attempt_n = 0
        sm_exists = False
        while attempt_n < 5:
            attempt_n += 1
            if not sm_exists: 
                try:
                    self.exec(sm_name + '_instance')
                    sm_exists = True
                except PyboardError as e:
                    err_message = e
            else:
                try: 
                    self.exec(sm_name + '_instance.smd.v.' + v_name)
                    return True # State machine and variable both exist.
                except PyboardError as e: 
                    err_message = e
        if sm_exists:
            print('Variable not set: invalid variable name.\n')
        else:
            print('Variable not set: invalid state machine name.\n')
        print('Pyboard error message: \n\n' + str(err_message))
        return False

    # ------------------------------------------------------------------------------------
    # Data logging
    # ------------------------------------------------------------------------------------

    def open_data_file(self, file_name, sub_dir = None):
        'Open a file to write pyControl data to.'
        if sub_dir:
            d_dir = os.path.join(data_dir, sub_dir)
        else:
            d_dir = data_dir
        if not os.path.exists(d_dir):
            os.mkdir(d_dir)
        self.file_path = os.path.join(d_dir, file_name)
        self.data_file = open(self.file_path, 'a+', newline = '\n')

    def close_data_file(self, copy_to_transfer = False):
        self.data_file.close()
        if copy_to_transfer: # Copy data file to transfer folder.
            shutil.copy2(self.file_path, os.path.join(data_dir, 'transfer'))
        self.data_file = None
        self.file_path = None