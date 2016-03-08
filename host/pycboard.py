from pyboard import Pyboard, PyboardError
import os
import time
import inspect

# ----------------------------------------------------------------------------------------
#  Default paths.
# ----------------------------------------------------------------------------------------

framework_dir = os.path.join('..', 'pyControl')
examples_dir  = os.path.join('..', 'examples')
tasks_dir     = os.path.join('..', 'tasks')
hwd_path      = os.path.join('.', 'config', 'hardware_definition.py')

# ----------------------------------------------------------------------------------------
#  Helper functions.
# ----------------------------------------------------------------------------------------
# Helper functions whose names start with an underscore are used on the pyboard not
# the host computer.  inspect.getsource is used to extract the function sourcecode.

# djb2 hashing algorithm used to check integrity of transfered files.

def djb2(string):
    h = 5381
    for c in string:
        h = ((h * 33) + ord(c)) & 0xFFFFFFFF
    return h

def _djb2_file(file_path):
    with open(file_path, 'r') as f:
        h = 5381
        while True:
            c = f.read(1)
            if not c:
                break
            h = ((h * 33) + ord(c)) & 0xFFFFFFFF           
    return h

# Used on pyboard to remove directories or files.
def _rm_dir_or_file(i):
    try:
        os.remove(i)
    except OSError:
        os.chdir(i)
        for j in os.listdir():
            _rm_dir_or_file(j)
        os.chdir('..')
        os.rmdir(i)

# Used on pyboard to clear filesystem.
def _reset_pyb_filesystem():
    os.chdir('/flash')
    for i in os.listdir():
        if i not in ['System Volume Information', 'boot.py']:
            _rm_dir_or_file(i)

# ----------------------------------------------------------------------------------------
#  Pycboard class.
# ----------------------------------------------------------------------------------------

class Pycboard(Pyboard):
    '''Pycontrol board inherits from Pyboard and adds functionality for file transfer
    and pyControl operations.
    '''

    def __init__(self, serial_port, number = None, baudrate=115200):
        self.serial_port = serial_port
        super().__init__(self.serial_port, baudrate=115200)
        self.reset() 
        self.unique_ID = eval(self.eval('pyb.unique_id()').decode())
        self.data_file = None
        self.number = number

    def reset(self):
        'Enter raw repl (soft reboots pyboard), import modules.'
        self.enter_raw_repl() # Soft resets pyboard.
        self.exec(inspect.getsource(_djb2_file))  # define djb2 hashing function.
        self.exec('import os; import gc')
        try:
            self.exec('from pyControl import *')
        except PyboardError:
            self.load_framework()
        self.framework_running = False
        self.data = None
        self.state_machines = [] # List to hold name of instantiated state machines.

    def hard_reset(self):
        print('Hard resetting pyboard.')
        self.serial.write(b'pyb.hard_reset()')
        self.close()     # Close serial connection.
        time.sleep(0.1)  # Wait 100 ms. 
        super().__init__(self.serial_port, baudrate=115200) # Reopen serial conection.
        self.reset()

    def gc_collect(self): 
        'Run a garbage collection on pyboard to free up memory.'
        self.exec('gc.collect()')

    # ------------------------------------------------------------------------------------
    # Pyboard filesystem operations.
    # ------------------------------------------------------------------------------------

    def write_file(self, target_path, data):
        '''Write data to file at specified path on pyboard, any data already
        in the file will be deleted.
        '''
        self.exec("tmpfile = open('{}','w')".format(target_path))
        self.exec("tmpfile.write({data})".format(data=repr(data)))
        self.exec('tmpfile.close()')

    def get_file_hash(self, target_path):
        'Get the djb2 hash of a file on the pyboard.'
        try:
            file_hash = int(self.eval("_djb2_file('{}')".format(target_path)).decode())
        except PyboardError as e: # File does not exist.
            return -1  
        return file_hash

    def transfer_file(self, file_path, target_path = None):
        '''Copy a file into the root directory of the pyboard.'''
        if not target_path:
            target_path = os.path.split(file_path)[-1]
        with open(file_path) as transfer_file:
            file_contents = transfer_file.read()  
        while not (djb2(file_contents) == self.get_file_hash(target_path)):
            self.write_file(target_path, file_contents) 
        self.gc_collect()
            
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

    def remove_file(self, file_path):
        'Remove a file from the pyboard.'
        self.exec('os.remove({})'.format(repr(file_path)))

    def reset_filesystem(self):
        '''Delete all files in the flash drive apart from boot.py, 
        then reload framework.'''
        print('Resetting filesystem.')
        self.reset()
        self.exec(inspect.getsource(_rm_dir_or_file))
        self.exec(inspect.getsource(_reset_pyb_filesystem)) 
        self.exec('_reset_pyb_filesystem()')
        self.hard_reset() 
        
    # ------------------------------------------------------------------------------------
    # pyControl operations.
    # ------------------------------------------------------------------------------------

    def load_framework(self, framework_dir = framework_dir):
        'Copy the pyControl framework folder to the board.'
        print('Transfering pyControl framework to pyboard.')
        self.transfer_folder(framework_dir, file_type = 'py')
        self.reset()

    def load_hardware_definition(self, hwd_path = hwd_path):
        '''Transfer a hardware definition file to pyboard.  Defaults to transfering 
        file hardware_definition.py from config folder.  File is renamed 
        hardware_definition.py in pyboard filesystem.'''
        if os.path.exists(hwd_path):
            print('Transfering hardware definition to pyboard.')
            self.transfer_file(hwd_path, target_path = 'hardware_definition.py')
            self.reset()
            try:
                self.exec('import hardware_definition')
            except PyboardError as e:
                print('Error: Unable to import hardware definition.\n' + e.args[2].decode())
        else:
            print('Hardware definition file not found.')  

    def setup_state_machine(self, sm_name, sm_dir = None, raise_exception = False):
        ''' Transfer state machine descriptor file sm_name.py from folder sm_dir
        (defaults to tasks_dir then examples_dir) to board. Instantiate state machine
        object as sm_name'''
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
        try:
            self.exec('import {} as smd'.format(sm_name))
            self.exec(sm_name + ' = sm.State_machine(smd)')
            self.state_machines.append(sm_name)  
        except PyboardError as e:
            print('Error: Unable to setup state machine.\n' + e.args[2].decode())
            if raise_exception:
                raise PyboardError('Unable to setup state machine.', e.args[2])
        self.remove_file(sm_name + '.py')

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
        time.sleep(0.1)
        self.process_data()

    def process_data(self):
        'Process data output from the pyboard to the serial line.'
        while self.serial.inWaiting() > 0:
            self.data = self.data + self.serial.read(1)  
            if self.data.endswith(b'\x04'): # End of framework run.
                self.framework_running = False
                data_err = self.read_until(2, b'\x04>', timeout=10) 
                if len(data_err) > 2:
                    print(data_err[:-3].decode())
                break
            elif self.data.endswith(b'\n'):  # End of data line.
                data_string = self.data.decode() 
                if self.number:
                    print('Box {}: '.format(self.number), end = '')
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

    def set_variable(self, v_name, v_value, sm_name = None):
        '''Set state machine variable with check that variable has not got corrupted 
        during transfer. If state machine name argument is not provided, default to
        the first instantiated state machine.'''
        if not sm_name: sm_name = self.state_machines[0]
        if not self._check_variable_exits(sm_name, v_name): return
        if v_value == None:
            print('Set variable aborted: value \'None\' not allowed.')
            return
        try:
            eval(repr(v_value))
        except:
            print('Set variable aborted: invalid variable value: ' + repr(v_value))
            return
        for i in range(10):
            try:
                self.exec(sm_name + '.smd.v.' + v_name + '=' + repr(v_value))
            except:
                pass 
            set_value = self.get_variable(v_name, sm_name, pre_checked = True)
            if self._approx_equal(set_value, v_value):
                return
        print('Set variable error: could not set variable: ' + v_name)

    def get_variable(self, v_name, sm_name = None, pre_checked = False):
        '''Get value of state machine variable.  To minimise risk of variable
        corruption during transfer, process is repeated until two consistent
        values are obtained. If state machine name argument is not provided, 
        default to the first instantiated  state machine.'''
        if not sm_name: sm_name = self.state_machines[0]
        if pre_checked or self._check_variable_exits(sm_name, v_name, op = 'Get'):
            v_value = None
            for i in range(10):
                prev_value = v_value
                try:
                    self.serial.flushInput()
                    v_value = eval(self.eval(sm_name + '.smd.v.' + v_name).decode())
                except:
                    pass
                if v_value != None and prev_value == v_value:
                    return v_value
        print('Get variable error: could not get variable: ' + v_name)

    def _check_variable_exits(self, sm_name, v_name, op = 'Set'):
        'Check if specified state machine has variable with specified name.'
        sm_found = False
        for i in range(10):
            if not sm_found: # Check if state machine exists.
                try: 
                    self.exec(sm_name)
                    sm_found = True
                except PyboardError:
                    pass
            else: # Check if variable exists.
                try: 
                    self.exec(sm_name + '.smd.v.' + v_name)
                    return True
                except PyboardError:
                    pass
        if sm_found:
            print(op + ' variable aborted: invalid variable name:' + v_name)
        else:
            print(op + ' variable aborted: invalid state machine name:' + sm_name)
        return False

    def _approx_equal(self, v, t):
        'Check two variables are the same up to floating point rounding errors.'
        if v == t: 
            return True
        elif (((type(t) == float) or (type(v) == float)) 
                and (abs(t - v) < (1e-5 + 1e-3 * abs(v)))):
            return True # Variable set within floating point accuracy.
        elif type(t) in (list, tuple) and all([_approx_equal(vi, ti) 
                                               for vi, ti in zip(v,t)]):
            return True
        elif type(t) == dict and all([_approx_equal(vi, ti)
                                      for vi, ti in zip(v.items(),t.items())]):
            return True
        else:
            return False
            
    # ------------------------------------------------------------------------------------
    # Data logging
    # ------------------------------------------------------------------------------------

    def open_data_file(self, file_path):
        'Open a file to write pyControl data to.'
        self.file_path = file_path
        self.data_file = open(self.file_path, 'a+', newline = '\n')

    def close_data_file(self):
        self.data_file.close()
        self.data_file = None
        self.file_path = None