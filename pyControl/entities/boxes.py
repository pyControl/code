# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" pycontrol.board.pyboard_plus"""

from pprint import pformat
import os
from time import sleep
import logging
from serial.serialutil import SerialException

import pycontrol
from pycontrol.board.pyboard import PyboardError
from pycontrol.entities.box import Box
from pycontrol.config import config as cf

__version__ = pycontrol.__version__
__author__ = pycontrol.__author__
__credits__ = pycontrol.__credits__
__license__ = pycontrol.__license__
__maintainer__ = pycontrol.__maintainer__
__email__ = pycontrol.__email__
__status__ = pycontrol.__status__

logger = logging.getLogger(__name__)


class HandlerBoxes(object):
    'Provides functionallity for doing operations on a group of Pycboards.'

    def __init__(self, box_numbers, experiment=None, data_dir=None, date=None):
        self.boxes = []
        self.experiment = experiment
        self.data_dir = data_dir
        self.date = date

        for box_n in box_numbers:

            print('Box {0}: Opening connection...'.format(box_n))
            box = Box(box_n, cf.box_serials[box_n])
            self.boxes.append(box)
            try:
                box.open_connection()
                print("Box {0}: Connected with ID: {1}".format(box.number, box.unique_ID))

                # if not box.framework_is_installed():
                #    print('Box {0}: Framework not installed!'.format(box.number))

            except PyboardError as err:
                logger.debug(str(err), exc_info=True)
                logger.warning("Box {}: Initialized with errors!".format(box_n))
                print('Box {0}: ERROR!'.format(box.number))

            except SerialException as err:
                logger.debug(str(err), exc_info=True)
                logger.warning("Box {}: Not connected!".format(box_n))
                print('Box {0}: ERROR!'.format(box.number))

    def info(self):
        for box in self.boxes:
            fw_installed = 'N/A'
            if box.is_connected():
                fw_installed = box.framework_is_installed()
            if box.unique_ID:
                bid = box.unique_ID
            else:
                bid = 'N/A'
            print("Box {0} | ID: {1} | Connected: {2} | FW Installed: {3}".format(box.number, bid, box.is_connected(),
                                                                                  fw_installed))

    def reconnect(self):
        """
        Tries to open connection for boxes that are disconnected
        :return:
        """
        for box in self.boxes:
            if not box.is_connected():
                try:
                    box.open_connection()
                    print("Box {0} connected with ID: {1}".format(box.number, box.unique_ID))
                except SerialException as err:
                    logger.debug(str(err))
                    print("WARNING: Box {} is not connected!".format(box.number))

    def reset(self):
        for box in self.boxes:
            try:
                box.reset_framework()
            except Exception as err:
                print("Cannot reset Box {0}: {1}".format(box.number, str(err)))

    def hard_reset(self):
        for box in self.boxes:
            try:
                print('Box {0}: Hard resetting...'.format(box.number))
                box.hard_reset()
                print('Box {0}: OK!'.format(box.number))
            except Exception as err:
                logger.debug(str(err), exc_info=True)
                logger.warning("Box {0}: Cannot load framework: {1}".format(box.number, str(err)))
                print('Box {0}: ERROR!'.format(box.number))

    def reset_filesystem(self):
        """
        Hard resets board and clears filesystem
        """
        for box in self.boxes:
            try:
                print('Box {0}: Resetting filesystem...'.format(box.number))
                box.reset_filesystem()
                print('Box {0}: OK!'.format(box.number))
            except Exception as err:
                logger.debug(str(err), exc_info=True)
                logger.warning("Box {0}: Cannot load framework: {1}".format(box.number, str(err)))
                print('Box {0}: ERROR!'.format(box.number))

    def upload_task(self, task_path):
        """
        Upload task for all boxes
        In case of failure in one box, action is aborted
        :param task_path:
        :return:
        """
        for box in self.boxes:
            box.upload_task(task_path)

    def update_hardware_definition(self):
        """
        Update hardware definition on each box.
        In case of failure in one box, tries to continue uploading for remaining boxes
        """
        for box in self.boxes:
            try:
                print('Box {0}: Update hardware definition...'.format(box.number))
                box.upload_hardware_definition(cf.hwd_path)
                print('Box {0}: OK!'.format(box.number))
            except Exception as err:
                logger.debug(str(err), exc_info=True)
                logger.warning("Box {0}: Cannot update hardware definition: {1}".format(box.number, str(err)))
                print('Box {0}: ERROR!'.format(box.number))

    def update_framework(self, override=False):
        """
        Upload new framework and overrides current one
        Loads framework after update
        :return:
        """
        for box in self.boxes:
            try:
                if box.framework_is_installed() and override is False:
                    print('Box {0}: Framework is installed. Skipping...'.format(box.number))
                else:
                    print('Box {0}: Uploading new framework...'.format(box.number))
                    box.upload_framework(cf.framework_dir)
                    print('Box {0}: OK!'.format(box.number))
            except Exception as err:
                logger.debug(str(err), exc_info=True)
                logger.warning("Box {0}: Cannot load framework: {1}".format(box.number, str(err)))
                print('Box {0}: ERROR!'.format(box.number))

    def process_data(self):
        """
        Collect and process data for each box
        :return:
        """
        for box in self.boxes:
            n_boxes_running = 0
            if box.framework_running:
                data_string = box.process_data()
                if data_string and box.data_file:
                    print("Box {0}: {1}".format(box.number, data_string.strip()))
                    if data_string.split(' ')[1][0] != '#':  # Output not a coment, write to file.
                        box.data_file.write(data_string)
                        box.data_file.flush()
                n_boxes_running += 1
        return n_boxes_running > 0

    def start_framework(self, dur=None, verbose=False, data_output=True, ISI=0.1):
        """
        Start framework on each box
        :param dur:
        :param verbose:
        :param data_output:
        :param ISI:
        :return:
        """
        for box in self.boxes:
            box.start_framework(dur, verbose, data_output)
            if ISI:
                sleep(ISI)  # Stagger start times by ISI seconds.
                box.process_data()

    def stop_framework(self):
        """
        Stop framework on each box
        """
        for box in self.boxes:
            box.stop_framework()

    def print_IDs(self):
        """
        Print IDs for each box
        """
        for box in self.boxes:
            box.print_IDs()

    def print_events(self):
        """
        Print events for each box
        """
        for box in self.boxes:
            events = box.get_events()
            print("Box {0}: {1}".format(box.number, events))

    def print_states(self):
        """
        Print IDs for each box
        """
        for box in self.boxes:
            states = box.get_states()
            print("Box {0}: {1}".format(box.number, states))

    def set_variable(self, v_name, v_value, sm_name=None):
        """
        Set specified variable on a all pycboards. If v_value is a
        dict whose keys include all the box ID numbers, the variable on each
        box is set to the corresponding value from the dictionary.  Otherwise
        the variable on all boxes is set to v_value.
        :param v_name:
        :param v_value:
        :param sm_name:
        :return:
        """

        all_boxes_numbers = [box.number for box in self.boxes]
        if type(v_value) == dict and set(all_boxes_numbers) <= set(v_value.keys()):
            try:
                for box in self.boxes:
                    box.set_variable(v_name, v_value[box.number], sm_name)
            except Exception as err:
                logger.warning("Box {0}: Cannot set variable: {1}".format(box.number, str(err)))
        else:
            try:
                for box in self.boxes:
                    box.set_variable(v_name, v_value, sm_name)
            except Exception as err:
                logger.warning("Box {0}: Cannot set variable: {1}".format(box.number, str(err)))

    def get_variable(self, v_name, sm_name=None):
        '''Get value of specified variable from all boxes and return as dict with
        box numbers as keys.'''
        v_values = {}
        for box in self.boxes:
            v_values[box.number] = box.get_variable(v_name, sm_name)
        return v_values

    def open_data_file(self):
        """

        :param data_dir:
        :param experiment:
        :param date:
        :return:
        """
        for box in self.boxes:
            data_file_path = os.path.join(self.data_dir, self.experiment.subjects[box.number] + self.date + '.txt')
            box.open_data_file(data_file_path)

    def close_data_file(self):
        for box in self.boxes:
            box.close_data_file()

    def close(self):
        """
        Close connection for all boxes
        """
        for box in self.boxes:
            box.close()

    def write_to_file(self, write_string):
        """
        Write string to file
        :param write_string:
        :return:
        """
        for box in self.boxes:
            box.data_file.write(write_string)

    def save_unique_IDs(self):
        """
        Save unique IDs of all boards on file
        :return:
        """
        print('Saving hardware unique IDs...')
        unique_IDs = [box.unique_ID for box in self.boxes]
        with open(os.path.join(cf.config_dir, 'hardware_unique_IDs.txt'), 'w') as id_file:
            id_file.write(pformat(unique_IDs))
        print('OK!')

    def check_unique_IDs(self):
        """
        Check whether hardware unique IDs of pyboards match those saved in
        config/hardware_unique_IDs.txt, if file not available no checking is performed.
        """

        try:
            with open(os.path.join(cf.config_dir, 'hardware_unique_IDs.txt'), 'r') as id_file:
                unique_IDs = eval(id_file.read())
        except FileNotFoundError:
            print('No hardware IDs saved, skipping hardware ID check.')
            return True
        print('Checking hardware IDs...  ', end='')
        IDs_OK = True
        for box in self.boxes:
            if unique_IDs[box.number - 1] != box.unique_ID:
                print('Box number {} does not match saved unique ID.'.format(box.number))
                IDs_OK = False
        if IDs_OK: print('IDs OK.')
        return IDs_OK
