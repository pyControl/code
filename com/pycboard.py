import os
import sys
import time
import inspect
from serial import SerialException
from array import array
from .pyboard import Pyboard, PyboardError
from config.paths import config_dir, framework_dir, devices_dir, tasks_dir

# ----------------------------------------------------------------------------------------
#  Helper functions.
# ----------------------------------------------------------------------------------------

# djb2 hashing algorithm used to check integrity of transfered files.
def _djb2_file(file_path):
    with open(file_path, 'rb') as f:
        h = 5381
        while True:
            c = f.read(4)
            if not c:
                break
            h = ((h << 5) + h + int.from_bytes(c,'little')) & 0xFFFFFFFF           
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

# Used on pyboard for file transfer.
def _receive_file(file_path, file_size):
    usb = pyb.USB_VCP()
    usb.setinterrupt(-1)
    buf_size = 512
    buf = bytearray(buf_size)
    buf_mv = memoryview(buf)
    bytes_remaining = file_size
    with open(file_path, 'wb') as f:
        while bytes_remaining > 0:
            bytes_read = usb.recv(buf, timeout=5)
            usb.write(b'0')
            if bytes_read:
                bytes_remaining -= bytes_read
                f.write(buf_mv[:bytes_read])

# ----------------------------------------------------------------------------------------
#  Pycboard class.
# ----------------------------------------------------------------------------------------

class Pycboard(Pyboard):
    '''Pycontrol board inherits from Pyboard and adds functionality for file transfer
    and pyControl operations.
    '''

    def __init__(self, serial_port,  baudrate=115200, verbose=True, raise_exception=True):
        self.serial_port = serial_port
        self.status = {'serial': None, 'framework':None, 'hardware':None, 'usb_mode':None}
        try:    
            super().__init__(self.serial_port, baudrate=115200)
            self.status['serial'] = True
            self.reset() 
            self.unique_ID = eval(self.eval('pyb.unique_id()').decode())
            v_tuple = eval(self.eval(
            "sys.implementation.version if hasattr(sys, 'implementation') else (0,0,0)").decode())
            self.micropython_version = float('{}.{}{}'.format(*v_tuple))
        except SerialException as e:
            if raise_exception:
                raise(e)
            self.status['serial'] = False
        if verbose: # Print status.
            if self.status['serial']:
                print('Micropython version: {}'.format(self.micropython_version))
            else:
                print('Error: Unable to open serial connection.')
                return
            if self.status['framework']:
                print('pyControl Framework: OK')
            else:
                if self.status['framework'] is None:
                    print('pyControl Framework: Not loaded')
                else:
                    print('pyControl Framework: Import error')
                return
            if self.status['hardware']:
                print('Hardware definition: OK')
            else:
                if self.status['hardware'] is None:
                    print('Hardware definition: Not loaded')
                else:
                    print('Hardware definition: Import error')

    def reset(self):
        'Enter raw repl (soft reboots pyboard), import modules.'
        self.enter_raw_repl() # Soft resets pyboard.
        self.exec(inspect.getsource(_djb2_file))  # define djb2 hashing function.
        self.exec(inspect.getsource(_receive_file))  # define recieve file function.
        self.exec('import os; import gc; import sys; import pyb')
        self.framework_running = False
        self.state_machines = [] # List to hold name of instantiated state machines.
        error_message = None
        self.status['usb_mode'] = self.eval('pyb.usb_mode()').decode()
        try:
            self.exec('from pyControl import *; import devices')
            self.status['framework'] = True # Framework imported OK.
        except PyboardError as e:
            error_message = e.args[2].decode()
            if (("ImportError: no module named 'pyControl'" in error_message) or
                ("ImportError: no module named 'devices'"   in error_message)):
                self.status['framework'] = None # Framework not installed.
            else:
                self.status['framework'] = False # Framework import error.
        if self.status['framework']:
            try:
                self.exec('import hardware_definition')
                self.status['hardware'] = True # Hardware definition imported OK.
            except PyboardError as e:
                error_message = e.args[2].decode()
                if "ImportError: no module named 'hardware_definition'" in error_message:
                    self.status['hardware'] = None # Hardware definition not installed.
                else:
                    self.status['hardware'] = False # Hardware definition import error.
        return error_message

    def hard_reset(self, reconnect=True):
        print('Hard resetting pyboard.')
        try:
            self.exec_raw_no_follow('pyb.hard_reset()')
        except PyboardError:
            pass
        self.close()    # Close serial connection.
        if reconnect:
            time.sleep(5.)  # Wait 5 seconds before trying to reopen serial connection.
            try: 
                super().__init__(self.serial_port, baudrate=115200) # Reopen serial conection.
                self.reset()
            except SerialException:
                print('Unable to reopen serial connection.')
        else:
            print('Serial connection closed.')

    def gc_collect(self): 
        'Run a garbage collection on pyboard to free up memory.'
        self.exec('gc.collect()')
        time.sleep(0.01)

    def DFU_mode(self):
        'Put the pyboard into device firmware update mode.'
        self.exec('import pyb')
        try:
            self.exec_raw_no_follow('pyb.bootloader()')
        except PyboardError as e:
            pass # Error occurs on older versions of micropython but DFU is entered OK.
        print('Entered DFU mode, closing serial connection.')
        self.close()

    def disable_mass_storage(self):
        'Modify the boot.py file to make the pyboards mass storage invisible to the host computer.'
        print('Disabling mass storage.')
        self.write_file('boot.py', "import machine\nimport pyb\npyb.usb_mode('VCP')")
        self.hard_reset(reconnect=False)

    def enable_mass_storage(self):
        'Modify the boot.py file to make the pyboards mass storage visible to the host computer.'
        print('Enabling mass storage.')
        self.write_file('boot.py', "import machine\nimport pyb\npyb.usb_mode('VCP+MSC')")
        self.hard_reset(reconnect=False)

    # ------------------------------------------------------------------------------------
    # Pyboard filesystem operations.
    # ------------------------------------------------------------------------------------

    def write_file(self, target_path, data, raise_exception=True):
        '''Write data to file at specified path on pyboard, any data already
        in the file will be deleted.'''
        try:
            self.exec("with open('{}','w') as f: f.write({})".format(target_path, repr(data)))
        except PyboardError as e:
            if raise_exception:
                raise PyboardError(e)

    def get_file_hash(self, target_path):
        'Get the djb2 hash of a file on the pyboard.'
        try:
            file_hash = int(self.eval("_djb2_file('{}')".format(target_path)).decode())
        except PyboardError as e: # File does not exist.
            return -1  
        return file_hash

    def transfer_file(self, file_path, target_path=None):
        '''Copy file at file_path to location target_path on pyboard.'''
        if not target_path:
            target_path = os.path.split(file_path)[-1]
        file_size = os.path.getsize(file_path)
        file_hash = _djb2_file(file_path)
        try:
            for i in range(10):
                    if file_hash == self.get_file_hash(target_path):
                        return
                    self.exec_raw_no_follow("_receive_file('{}',{})"
                                            .format(target_path, file_size))
                    with open(file_path, 'rb') as f:
                        while True:
                            chunk = f.read(512)
                            if not chunk:
                                break
                            self.serial.write(chunk)
                            self.serial.read(1)
                    self.follow(5)
        except PyboardError as e:
            print('Error: Unable to transfer file')
            print(e)
            input('\nPress any key to close.')
            sys.exit()

    def transfer_folder(self, folder_path, target_folder=None, file_type='all',
                        show_progress=False):
        '''Copy a folder into the root directory of the pyboard.  Folders that
        contain subfolders will not be copied successfully.  To copy only files of
        a specific type, change the file_type argument to the file suffix (e.g. 'py').'''
        if not target_folder:
            target_folder = os.path.split(folder_path)[-1]
        files = os.listdir(folder_path)
        if file_type != 'all':
            files = [f for f in files if f.split('.')[-1] == file_type]
        try:
            self.exec('os.mkdir({})'.format(repr(target_folder)))
        except PyboardError:
            pass # Folder already exists.
        for f in files:
            file_path = os.path.join(folder_path, f)
            target_path = target_folder + '/' + f
            self.transfer_file(file_path, target_path)
            if show_progress:
                print('.', end='')
                sys.stdout.flush()

    def remove_file(self, file_path):
        'Remove a file from the pyboard.'
        self.exec('os.remove({})'.format(repr(file_path)))

    def reset_filesystem(self):
        '''Delete all files in the flash drive apart from boot.py'''
        print('Resetting filesystem.')
        self.reset()
        self.exec(inspect.getsource(_rm_dir_or_file))
        self.exec(inspect.getsource(_reset_pyb_filesystem)) 
        self.exec_raw('_reset_pyb_filesystem()', timeout=60)
        self.hard_reset() 
        
    # ------------------------------------------------------------------------------------
    # pyControl operations.
    # ------------------------------------------------------------------------------------

    def load_framework(self, framework_dir = framework_dir):
        'Copy the pyControl framework folder to the board.'
        print('Transfering pyControl framework to pyboard.', end='')
        self.transfer_folder(framework_dir, file_type='py', show_progress=True)
        self.transfer_folder(devices_dir  , file_type='py', show_progress=True)
        print('')
        error_message = self.reset()
        if not self.status['framework']:
            print('Error importing framework:')
            print(error_message)
        return 

    def load_hardware_definition(self, hwd_path=os.path.join(config_dir, 'hardware_definition.py')):
        '''Transfer a hardware definition file to pyboard.  Defaults to transfering 
        file hardware_definition.py from config folder. '''
        if os.path.exists(hwd_path):
            print('Transfering hardware definition to pyboard.')
            self.transfer_file(hwd_path, target_path = 'hardware_definition.py')
            error_message = self.reset()
            if not self.status['hardware']:
                print('Error importing hardware definition:')
                print(error_message)
        else:
            print('Hardware definition file not found.') 

    def setup_state_machine(self, sm_name, sm_dir=tasks_dir, raise_exception=True):
        ''' Transfer state machine descriptor file sm_name.py from folder sm_dir
        to board. Instantiate state machine object as sm_name'''
        self.reset()
        sm_path = os.path.join(sm_dir, sm_name + '.py')
        if not os.path.exists(sm_path):
            print('Error: State machine file not found at: ' + sm_path)
            if raise_exception:
                raise PyboardError('State machine file not found at: ' + sm_path)
            return
        print('Transfering state machine {} to pyboard.'.format(repr(sm_name)))
        self.transfer_file(sm_path)
        try:
            self.exec('import {} as smd'.format(sm_name))
            self.exec(sm_name + ' = sm.State_machine(smd)')
            self.state_machines.append(sm_name)  
        except PyboardError as e:
            print('\nError: Unable to setup state machine.\n\n' + e.args[2].decode())
            if raise_exception:
                raise PyboardError('Unable to setup state machine.', e.args[2])
        self.remove_file(sm_name + '.py')
        # Get information about state machine.
        sm_info = {'states': self.get_states(),
                   'events': self.get_events(),
                   'analog_inputs': self.get_analog_inputs()}
        return sm_info

    def get_states(self):
        'Return states as a dictionary {state_name: state_ID}'
        return eval(self.exec('fw.get_states()').decode().strip())

    def get_events(self):
        'Return events as a dictionary {event_name: state_ID}'
        return eval(self.exec('fw.get_events()').decode().strip())

    def get_analog_inputs(self):
        'Return analog_inputs as a directory {input name: ID}'
        return eval(self.exec('hw.get_analog_inputs()').decode().strip())

    def start_framework(self, dur=None, data_output=True):
        'Start pyControl framwork running on pyboard.'
        self.exec('fw.data_output = ' + repr(data_output))
        self.exec_raw_no_follow('fw.run({})'.format(dur))
        self.framework_running = True

    def stop_framework(self):
        'Stop framework running on pyboard by sending stop command.'
        self.serial.write(b'E')
        self.framework_running = False

    def process_data(self, raise_exception=True):
        'Read data from serial line and return list of data tuples.'
        new_data = []
        while self.serial.inWaiting() > 0:
            new_byte = self.serial.read(1)  
            if new_byte == b'A': # Analog data, 13 byte header + variable size content.
                data_header = self.serial.read(13)
                typecode      = data_header[0:1].decode()             
                ID            = int.from_bytes(data_header[1:3], 'little')
                sampling_rate = int.from_bytes(data_header[3:5], 'little')
                n_bytes       = int.from_bytes(data_header[5:7], 'little')
                timestamp     = int.from_bytes(data_header[7:11], 'little')
                checksum      = int.from_bytes(data_header[11:13], 'little')
                data_array    = array(typecode, self.serial.read(n_bytes))
                if checksum == (sum(data_header[:-2]) + sum(data_array)) & 0xffff: # Checksum OK.
                    new_data.append(('A',ID, sampling_rate, timestamp, data_array))
                else:
                    new_data.append(('!','bad checksum A'))
            elif new_byte == b'D': # Event or state entry, 8 byte data header only.
                data_header = self.serial.read(8)
                timestamp = int.from_bytes(data_header[ :4], 'little')
                ID        = int.from_bytes(data_header[4:6], 'little')
                checksum  = int.from_bytes(data_header[6:8], 'little')
                if checksum == sum(data_header[:-2]): # Checksum OK.
                    new_data.append(('D',timestamp, ID))
                else:
                    new_data.append(('!','bad checksum D'))
            elif new_byte == b'P': # User print statement, 8 byte data header + variable size content.
                data_header = self.serial.read(8)
                n_bytes   = int.from_bytes(data_header[ :2], 'little')
                timestamp = int.from_bytes(data_header[2:6], 'little')
                checksum  = int.from_bytes(data_header[6:8], 'little')
                print_string = self.serial.read(n_bytes)
                if checksum == (sum(data_header[:-2]) + sum(print_string)) & 0xffff: # Checksum OK.
                    new_data.append(('P',timestamp, print_string.decode()))
                else:
                    new_data.append(('!','bad checksum P'))
            elif new_byte == b'\x04': # End of framework run.
                self.framework_running = False
                data_err = self.read_until(2, b'\x04>', timeout=10) 
                if len(data_err) > 2:
                    error_string = data_err[:-3].decode()
                    self.reset() # Reset board to turn off all output.                      
                    if raise_exception:
                        raise PyboardError(error_string)
                    else:
                        print(error_string)
                break
        return new_data

    def run_framework(self, dur=None, raise_exception=True):
        '''Run framework for specified duration (seconds).'''
        self.start_framework(dur)
        try:
            while self.framework_running:
                self.process_data(raise_exception=raise_exception)     
        except KeyboardInterrupt:
            self.stop_framework()
        time.sleep(0.1)
        self.process_data(raise_exception=raise_exception)

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
            print('\nSet variable aborted - value \'None\' not allowed.')
            return
        try:
            eval(repr(v_value))
        except:
            print('\nSet variable aborted - invalid variable value: ' + repr(v_value))
            return
        for i in range(10):
            try:
                self.exec(sm_name + '.smd.v.' + v_name + '=' + repr(v_value))
            except:
                pass 
            set_value = self.get_variable(v_name, sm_name, pre_checked = True)
            if self._approx_equal(set_value, v_value):
                return True
        print('\nSet variable error - could not set variable: ' + v_name)
        return

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
                    v_string = self.eval(sm_name + '.smd.v.' + v_name).decode()
                except PyboardError:
                    continue
                try:
                    v_value = eval(v_string)
                except NameError:
                    v_value = v_string
                if v_value != None and prev_value == v_value:
                    return v_value
            print('\nGet variable error - could not get variable: ' + v_name)

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
            print('\n'+ op + ' variable aborted: invalid variable name:' + v_name)
        else:
            print('\n'+ op + ' variable aborted: invalid state machine name:' + sm_name)
        return False

    def _approx_equal(self, v, t):
        'Check two variables are the same up to floating point rounding errors.'
        if v == t: 
            return True
        elif (((type(t) == float) or (type(v) == float)) 
                and (abs(t - v) < (1e-5 + 1e-3 * abs(v)))):
            return True # Variable set within floating point accuracy.
        elif type(t) in (list, tuple) and all([self._approx_equal(vi, ti) 
                                               for vi, ti in zip(v,t)]):
            return True
        elif type(t) == dict and all([self._approx_equal(vi, ti)
                                      for vi, ti in zip(v.items(),t.items())]):
            return True
        else:
            return False