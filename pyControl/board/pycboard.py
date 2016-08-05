# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" pycontrol.board.pyboard_plus"""

import os
import time
import logging

import pycontrol
from pycontrol.board.pyboard import PyboardError
from pycontrol.board.pyboard_plus import PyboardPlus

__version__ = pycontrol.__version__
__author__ = pycontrol.__author__
__credits__ = pycontrol.__credits__
__license__ = pycontrol.__license__
__maintainer__ = pycontrol.__maintainer__
__email__ = pycontrol.__email__
__status__ = pycontrol.__status__

logger = logging.getLogger(__name__)

FRAMEWORK_NAME = 'pyControl'


class PycboardError(Exception):
    def __init__(self, value, board_exception=None):
        self.value = value
        self.board_exception = board_exception

    def __str__(self):
        return self.value


# ----------------------------------------------------------------------------------------
#  Pycboard class.
# ----------------------------------------------------------------------------------------
class Pycboard(PyboardPlus):
    """
    Pycboard inherits from PyboardPlus and adds functionality for pyControl operations.
    """

    def __init__(self, serial_port, baudrate=115200):
        logger.debug("ACTION: Init board")

        super().__init__(serial_port, baudrate)

    # ------------------------------------------------------------------------------------
    # pyControl operations.
    # ------------------------------------------------------------------------------------

    def framework_is_installed(self):
        """
        Check if framework folder exists on board and if it is not empty
        :return: True if exists False otherwise
        """
        logger.debug("ACTION: Checking for framework dir on board")

        framework_is_installed = False

        framework_is_installed = self.folder_exists(FRAMEWORK_NAME) and self.folder_len(FRAMEWORK_NAME) > 0

        return framework_is_installed

    def reset(self):
        """
        Soft reset board and reload framework if available
        Don't raise exception if framework is corrupted because open_connection calls
        reset and it would fail before we could call the reset_filesystem
        """
        PyboardPlus.reset(self)

        if self.framework_is_installed():
            logger.debug("ACTION: Load framework")
            try:
                self.exec('from {0} import *'.format(FRAMEWORK_NAME))
                self.framework_running = False
                self.data = None
                self.state_machines = []  # List to hold name of instantiated state machines.
                logger.debug("Framework succesfully loaded")
            except PyboardError as err:
                logger.warning("Framework is installed but it is corrupted.")

    def upload_framework(self, framework_dir):
        """
        Hard resets board and clears filesystem
        Then, copy the pyControl framework folder to the board.
        Finally resets framework
        :param framework_dir:
        :raises FileNotFoundError if framework_dir is invalid
        :raises SerialException if board is not connected
        """

        logger.debug('ACTION: Upload pyControl framework')
        self.reset_filesystem()
        self.transfer_folder(framework_dir, file_type='py')
        self.reset()
        logger.debug('Success!')

    def upload_hardware_definition(self, hwd_path, remove_after_install=True):
        """
        Transfer a hardware definition file to pyboard.
        File is renamed hardware_definition.py in pyboard filesystem.
        Pre-condition: os.path.exists(hwd_path)
        :param hwd_path:
        :raises FileNotFoundError if hwd_path is invalid
        :raises SerialException if board is not connected
        """
        logger.debug('ACTION: Transfer hardware definition')
        self.transfer_file(hwd_path, target_path='hardware_definition.py')
        self.reset()

        try:
            self.exec('import hardware_definition')
        except PyboardError as err:
            raise PycboardError("Framework not installed", err)

        logger.debug('Success!')

        if remove_after_install:
            self.remove_file("hardware_definition.py")
            logger.debug("File removed from board.")

    def upload_task(self, task_file_path, remove_after_install=True):
        """
        Uploads and installs task (state machine) on board
        Pre-condition: os.path.exists(task_file_path)
        :param task_file_path:
        :param remove_after_install: remove task file after correctly loaded
        :raises FileNotFoundError if task_file_path is invalid
        :raises SerialException if board is not connected
        :raises PycboardError if framework is not installed
        :raises PyboardError if other board error
        """

        logger.debug('ACTION: Upload task')

        _, tail = os.path.split(task_file_path)
        task_name = os.path.splitext(tail)[0]
        logger.debug("Task name: %s", task_name)

        self.transfer_file(task_file_path)
        self.reset()

        try:
            self.exec('import {} as smd'.format(task_name))
        except PyboardError as err:
            raise PycboardError("Framework not installed", err)

        self.exec(task_name + ' = sm.State_machine(smd)')
        self.state_machines.append(task_name)

        logger.debug("Task successfully installed")

        if remove_after_install:
            self.remove_file(task_name + '.py')
            logger.debug("File removed from board.")

    def get_IDs(self):
        """
        Get state and event IDs.
        :return:
        """
        logger.debug("ACTION: Get IDs")
        return self.exec('fw.print_IDs()').decode()

    def get_states(self):
        """
        Return states as a dictionary
        """
        logger.debug("ACTION: Get states")
        return self.exec('fw.print_states()').decode().strip()

    def get_events(self):
        """
        Return events as a dictionary
        """
        logger.debug("ACTION: Get events")
        return self.exec('fw.print_events()').decode().strip()

    def start_framework(self, dur=None, verbose=False, data_output=True):
        'Start pyControl framwork running on pyboard.'
        logger.debug("ACTION: start framework")
        self.exec('fw.verbose = ' + repr(verbose))
        self.exec('fw.data_output = ' + repr(data_output))
        self.exec_raw_no_follow('fw.run({})'.format(dur))
        self.framework_running = True
        self.data = b''

    def stop_framework(self):
        'Stop framework running on pyboard by sending stop command.'
        logger.debug("ACTION: stop framework")
        self.serial.write(b'E')
        self.framework_running = False
        time.sleep(0.1)

    def process_data(self):
        'Process data output from the pyboard to the serial line.'
        data_ok = None
        while self.serial.inWaiting() > 0:
            self.data = self.data + self.serial.read(1)
            if self.data.endswith(b'\x04'):  # End of framework run.
                self.framework_running = False
                end_data = self.read_until(2, b'\x04>', timeout=10)
                if len(end_data) > 2:
                    logger.warning(end_data[:-3].decode())
                    raise PycboardError("End of framework run has errors: {0}".format(end_data.decode()))
                break
            elif self.data.endswith(b'\n'):  # End of data line.
                data_ok = self.data.decode()
                self.data = b''

        return data_ok

    def run_framework(self, dur=None, verbose=False):
        '''Run framework for specified duration (seconds).'''
        self.start_framework(dur, verbose)
        try:
            while self.framework_running:
                self.process_data()
        except KeyboardInterrupt:
            self.stop_framework()

    def run_state_machine(self, sm_name, dur, sm_dir=None, verbose=False):
        '''Run the state machine sm_name from directory sm_dir for the specified 
        duration (seconds).
        '''
        self.setup_state_machine(sm_name, sm_dir)
        self.run_framework(dur, verbose)

    # ------------------------------------------------------------------------------------
    # Getting and setting variables.
    # ------------------------------------------------------------------------------------

    def set_variable(self, v_name, v_value, sm_name=None):
        """
        Set state machine variable with check that variable has not got corrupted
        during transfer. If state machine name argument is not provided, default to
        the first instantiated state machine.
        :param v_name: variable name
        :param v_value: variable value
        :param sm_name: state machine name (task)
        :raises PycboardError if cannot set variable on board
        """
        logger.debug("ACTION: set variable")

        set_var_success = False

        if not sm_name:
            if not len(self.state_machines):
                raise PycboardError("Set variable aborted: state machine not specified.")
            sm_name = self.state_machines[0]
        if not self._check_variable_exits(sm_name, v_name):
            raise PycboardError("Set variable aborted: variable name {0} not found.".format(v_name))
        if v_value is None:
            raise PycboardError('Set variable aborted: value \'None\' not allowed.')
        try:
            eval(repr(v_value))
        except Exception as err:
            raise PycboardError('Set variable aborted: invalid variable value', err)

        logger.debug("Name: %s | Value: %s ", v_name, v_value)

        retries = 10
        for i in range(retries):
            try:
                self.exec(sm_name + '.smd.v.' + v_name + '=' + repr(v_value))
            except Exception as err:
                raise PycboardError('Set variable aborted: could not set value on board', err)
            set_value = self.get_variable(v_name, sm_name, pre_checked=True)
            if self._approx_equal(set_value, v_value):
                logger.debug("Variable successfully updated")
                set_var_success = True
                break

        if not set_var_success:
            raise PycboardError('Set variable error: variable value on board does not match')

    def get_variable(self, v_name, sm_name=None, pre_checked=False):
        """
        Get value of state machine variable.  To minimise risk of variable
        corruption during transfer, process is repeated until two consistent
        values are obtained or number of retries is exceeded. If state machine name argument is not provided,
        default to the first instantiated  state machine.
        :param v_name:
        :param sm_name:
        :param pre_checked:
        :raises PycboardError if cannot get variable on board
        :return: variable value (string)
        """
        logger.debug("ACTION: get variable value")
        logger.debug("Name: %s", v_name)
        if not sm_name:
            if not len(self.state_machines):
                raise PycboardError("Get variable aborted: state machine not specified.")
            sm_name = self.state_machines[0]
        if pre_checked or self._check_variable_exits(sm_name, v_name, op='Get'):
            v_value = None
            retries = 20
            for i in range(retries):
                prev_value = v_value
                try:
                    self.serial.flushInput()
                    v_value = eval(self.eval(sm_name + '.smd.v.' + v_name).decode())
                except:
                    pass
                if v_value is not None and prev_value == v_value:
                    logger.debug("Variable value: %s", v_value)
                    return v_value

        raise PycboardError("Get variable error: could not get variable name {0}.".format(v_name))

    # PRIVATE METHODS

    def _check_variable_exits(self, sm_name, v_name, op='Set'):
        """
        Check if specified state machine has variable with specified name.
        :param sm_name:
        :param v_name:
        :param op:
        :return:
        """

        sm_found = False
        for i in range(10):
            if not sm_found:  # Check if state machine exists.
                try:
                    self.exec(sm_name)
                    sm_found = True
                except Exception as err:
                    logger.debug(str(err))
            else:  # Check if variable exists.
                try:
                    self.exec(sm_name + '.smd.v.' + v_name)
                    return True
                except Exception as err:
                    logger.debug(str(err))
        if sm_found:
            logger.warning(op + ' variable aborted: invalid variable name: ' + v_name)
        else:
            logger.warning(op + ' variable aborted: invalid state machine name: ' + sm_name)
        return False

    def _approx_equal(self, v, t):
        """
        Check two variables are the same up to floating point rounding errors.
        :param v:
        :param t:
        :return:
        """

        if v == t:
            return True
        elif (((type(t) == float) or (type(v) == float))
              and (abs(t - v) < (1e-5 + 1e-3 * abs(v)))):
            return True  # Variable set within floating point accuracy.
        elif type(t) in (list, tuple) and all([self._approx_equal(vi, ti)
                                               for vi, ti in zip(v, t)]):
            return True
        elif type(t) == dict and all([self._approx_equal(vi, ti)
                                      for vi, ti in zip(v.items(), t.items())]):
            return True
        else:
            return False
