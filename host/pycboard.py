from pyboard import Pyboard, PyboardError
import os
import shutil
import time
try:
    import config.config as cf
except ImportError: # User created config file not present.
    import example_config.config as cf
   
# ----------------------------------------------------------------------------------------
#  # djb2 hashing algorithm used to check file transfer integrity.
# ----------------------------------------------------------------------------------------

def djb2(string):  
    h = 5381
    for c in string:
        h = ((h * 33) + ord(c)) & 0xFFFFFFFF
    return h

djb2_exec = ''' 
def djb2(string):
    h = 5381
    for c in string:
        h = ((h * 33) + ord(c)) & 0xFFFFFFFF
    return h
''' # String used to define djb2 function on pyboard.

# ----------------------------------------------------------------------------------------
#  Pycboard class.
# ----------------------------------------------------------------------------------------

class Pycboard(Pyboard):
    '''Pycontrol board inherits from Pyboard and adds functionallity for file transfer
    and pyControl operations.
    '''

    def __init__(self, serial_device, number = None, baudrate=115200):
        super().__init__(serial_device, baudrate=115200)
        self.reset() 
        self.unique_ID = eval(self.eval('pyb.unique_id()').decode())
        self.data_file = None
        self.number = number

    def reset(self):
        'Enter raw repl (soft reboots pyboard), import modules.'
        self.enter_raw_repl() # Soft resets pyboard.
        self.exec(djb2_exec)  # define djb2 hashing function.
        try:
            self.exec('from pyControl import *;import os')
        except PyboardError:
            self.load_framework()
        self.framework_running = False
        self.data = None
        self.state_machines = [] # List to hold name of instantiated state machines.

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
        with open(file_path) as transfer_file:
            file_contents = transfer_file.read()  
        while not (djb2(file_contents) == self.get_file_hash(target_path)):
            self.write_file(target_path, file_contents) 

    def get_file_hash(self, target_path):
        'Get the djb2 hash of a file on the pyboard.'
        try:
            self.exec("tmpfile = open('{}','r')".format(target_path))
            file_hash = int(self.eval('djb2(tmpfile.read())').decode())
            self.exec('tmpfile.close()')
        except PyboardError as e: # File does not exist.
            return -1  
        return file_hash

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
        print('Transfering pyControl framework to pyboard.', end = '')
        self.transfer_folder(cf.pyControl_dir, file_type = 'py')
        self.reset()

    def load_hardware_definition(self, hwd_name = 'hardware_definition', hwd_dir = cf.config_dir):
        '''Transfer a hardware definition file to pyboard.  Defaults to transfering file
        hardware_definition.py from config folder.  If annother file is specified, that
        file is transferred and given name hardware_definition.py in pyboard filesystem.'''
        hwd_path = os.path.join(hwd_dir, hwd_name + '.py')
        if os.path.exists(hwd_path):
            print('Transfering hardware definition to pyboard.')
            self.transfer_file(hwd_path, target_path = 'hardware_definition.py')
            self.reset()
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
        (defaults to cf.tasks_dir then cf.examples_dir) to board. Instantiate state machine object
        as sm_name'''
        self.reset()
        if not sm_dir:
            if os.path.exists(os.path.join(cf.tasks_dir, sm_name + '.py')):
                sm_dir = cf.tasks_dir
            else:
                sm_dir = cf.examples_dir
        sm_path = os.path.join(sm_dir, sm_name + '.py')
        assert os.path.exists(sm_path), 'State machine file not found at: ' + sm_path
        print('Transfering state machine {} to pyboard.'.format(repr(sm_name)))
        self.transfer_file(sm_path)
        try:
            self.exec('import ' + sm_name + ' as ' + sm_name + '_smd') 
        except PyboardError as e:
            raise PyboardError('Unable to import state machine definition.', e.args[2])
        self.remove_file(sm_name + '.py')
        self.exec(sm_name + ' = sm.State_machine({})'.format(sm_name + '_smd'))
        self.state_machines.append(sm_name)

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
                    print(data_err.decode())
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
        '''Set state machine variable when framework not running, check  variable
        has not got corrupted during setting. If state machine name argument is not
        provided, default to the first created state machine.'''
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
        for attempt_n in range(5):
            try:
                self.exec(sm_name + '.smd.v.' + v_name + '=' + repr(v_value))
            except PyboardError as e:
                print(e) 
            set_value = self.get_variable(v_name, sm_name, pre_checked = True)
            if self._approx_equal(set_value, v_value):
                return
        print('Set variable error: could not set variable: ' + v_name)

    def get_variable(self, v_name, sm_name = None, pre_checked = False):
        '''Get value of state machine variable when framework not running. If state
        machine name argument is not provided, default to the first created state machine.'''
        if not sm_name: sm_name = self.state_machines[0]
        if pre_checked or self._check_variable_exits(sm_name, v_name, op = 'Get'):
            attempt_n, v_string, v_value = (0, None, None)
            for attempt_n in range(5):
                try:
                    self.serial.flushInput()
                    v_string = self.eval(sm_name + '.smd.v.' + v_name).decode()
                except PyboardError as e:
                    print(e) 
                if v_string is not None:
                    try:
                        v_value = eval(v_string)
                        if v_value is not None:
                            return v_value
                    except:
                        if attempt_n == 5:
                            print('Get variable error: unable to eval string: ' + v_string)
            print('Get variable error: could not get variable: ' + v_name)

    def _check_variable_exits(self, sm_name, v_name, op = 'Set'):
        sm_found = False
        for attempt_n in range(5):
            if sm_found: # Check if variable exists.
                try: 
                    self.exec(sm_name + '.smd.v.' + v_name)
                    return True
                except PyboardError:
                    pass
            else: # Check if state machine exists. 
                try:
                    self.exec(sm_name)
                    sm_found = True
                except PyboardError:
                    pass
        if sm_found:
            print(op + ' variable aborted: invalid variable name.\n')
        else:
            print(op + ' variable aborted: invalid state machine name.\n')
        return False

    def _approx_equal(self, v, t): # Check for equality given floating point rounding.
        if v == t: 
            return True
        elif ((type(t) == float) or (type(v) == float) 
                    and ((abs(t - v) / max(t,v,0.01) < 0.0001))):
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

    def open_data_file(self, file_name, sub_dir = None):
        'Open a file to write pyControl data to.'
        if sub_dir:
            d_dir = os.path.join(cf.data_dir, sub_dir)
        else:
            d_dir = cf.data_dir
        if not os.path.exists(d_dir):
            os.mkdir(d_dir)
        self.file_path = os.path.join(d_dir, file_name)
        self.data_file = open(self.file_path, 'a+', newline = '\n')

    def close_data_file(self):
        self.data_file.close()
        if cf.transfer_dir: # Copy data file to transfer folder.
            shutil.copy2(self.file_path, cf.transfer_dir)
        self.data_file = None
        self.file_path = None