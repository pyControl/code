# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" pycontrol.board.pyboard_plus"""

import pycontrol
from pycontrol.board.pyboard import Pyboard, PyboardError
import os
import time
import inspect
import logging

__version__ = pycontrol.__version__
__author__ = pycontrol.__author__
__credits__ = pycontrol.__credits__
__license__ = pycontrol.__license__
__maintainer__ = pycontrol.__maintainer__
__email__ = pycontrol.__email__
__status__ = pycontrol.__status__

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------------------
#  Helper functions.
# ----------------------------------------------------------------------------------------

# djb2 hashing algorithm used to check integrity of transfered files.

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


class PyboardPlus(Pyboard):
    """
    PyboardPlus inherits from Pyboard and adds functionality for file transfer.
    NOTE: DO NOT WRITE ANY PYCONTROL SPECIFIC CODE HERE
    """

    def __init__(self, serial_port, number=None, baudrate=115200):
        super().__init__(serial_port, baudrate)
        self.unique_ID = ''

    def open_connection(self):
        logger.debug("Opening serial port: %s", self.serial_port)
        Pyboard.open_connection(self)

        self.reset()
        self.unique_ID = eval(self.eval('pyb.unique_id()').decode())
        logger.debug("Board uid: %s", self.unique_ID)

    def reset(self):
        'Enter raw repl (soft reboots pyboard), import modules.'
        logger.debug("Soft resetting board...")
        self.enter_raw_repl()  # Soft resets pyboard.
        self.exec(inspect.getsource(_djb2_file))  # define djb2 hashing function.
        self.exec('import os; import gc; import pyb')

    def hard_reset(self):
        logger.debug('Hard resetting pyboard.')
        self.serial.write(b'pyb.hard_reset()')
        self.close()  # Close serial connection.
        time.sleep(0.1)  # Wait 100 ms.
        self.open_connection()  # Reopen serial conection.
        self.reset()

    def gc_collect(self):
        'Run a garbage collection on pyboard to free up memory.'
        self.exec('gc.collect()')

    # ------------------------------------------------------------------------------------
    # Pyboard filesystem operations.
    # ------------------------------------------------------------------------------------

    def write_file(self, target_path, data):
        """
        Write data to file at specified path on pyboard, any data already
        in the file will be deleted.
        :param target_path: where to save file and desired name
        :param data: data content
        """
        self.exec("tmpfile = open('{}','w')".format(target_path))
        try:
            self.exec("tmpfile.write({})".format(repr(data)))
        except PyboardError as err:
            logger.error('Write file error.', exc_info=True)
        self.exec('tmpfile.close()')

    def get_file_hash(self, target_path):
        'Get the djb2 hash of a file on the pyboard.'
        return int(self.eval("_djb2_file('{}')".format(target_path)).decode())

    def transfer_file(self, file_path, target_path=None):
        """
        Copy a file into the root directory of the pyboard.
        :param file_path: full path to file to be transferred
        :param target_path: where to save file and desired name
        """
        logger.debug("Transfering file: %s", file_path)
        if not target_path:
            target_path = os.path.split(file_path)[-1]
        file_hash = _djb2_file(file_path)

        with open(file_path, 'r') as transfer_file:
            file_contents = transfer_file.read()

        retries = 3
        for i in range(retries):
            self.write_file(target_path, file_contents)
            hash_verification = file_hash == self.get_file_hash(target_path)
            if hash_verification:
                break

        if not hash_verification:
            raise PyboardError("File transfer hash doesn't match")

        logger.debug("Hash verification: %s. Number of tries: %s", hash_verification, i+1)

        self.gc_collect()

    def transfer_folder(self, folder_path, target_folder=None, file_type='all'):
        """
        Copy a folder into the root directory of the pyboard.  Folders that
        contain subfolders will not be copied successfully.  To copy only files of
        a specific type, change the file_type argument to the file suffix (e.g. 'py').
        WARNING: this operation always overrides if folder_path already exists!
        :param folder_path: full path to folder that is to be transferred
        :param target_folder: where to save folder and desired name
        :param file_type: filter files by extension
        :return:
        """
        logger.debug("Transfering folder to board: %s", folder_path)
        if not target_folder:
            target_folder = os.path.split(folder_path)[-1]
        files = os.listdir(folder_path)
        if file_type != 'all':
            files = [f for f in files if f.split('.')[-1] == file_type]
        logger.debug("Files to upload: %s", str(files))

        self.exec('import os;')

        folder_exists = False
        try:
            self.exec('os.listdir({})'.format(repr(target_folder)))
            folder_exists = True
        except PyboardError as err:  # if cannot list, is because the folder doesn't exist or is corrupted
            pass

        if not folder_exists:
            try:
                self.exec('os.remove({})'.format(repr(target_folder)))
                logger.debug("Corrupted folder removed!")
            except PyboardError as err:
                pass  # the folder doesn't exist so just go on

        try:
            self.exec('os.mkdir({})'.format(repr(target_folder)))
        except PyboardError as err:
            logger.warning(str(err))

        for f in files:
            file_path = os.path.join(folder_path, f)
            target_path = target_folder + '/' + f
            self.transfer_file(file_path, target_path)

    def remove_file(self, file_path):
        'Remove a file from the pyboard.'
        self.exec('os.remove({})'.format(repr(file_path)))

    def reset_filesystem(self):
        """
        Delete all files in the flash drive apart from boot.py
        :return:
        """
        logger.debug('Resetting filesystem...')
        self.reset()
        self.exec(inspect.getsource(_rm_dir_or_file))
        self.exec(inspect.getsource(_reset_pyb_filesystem))
        self.exec('_reset_pyb_filesystem()')
        self.hard_reset()

    def folder_exists(self, folder_path):
        """
        Check if folder exists on board
        :param folder_path:
        :return:
        """
        try:
            self.exec('os.listdir({})'.format(repr(folder_path)))
            return True
        except PyboardError as err:
            logger.debug(str(err))
            pass

        return False

    def folder_len(self, folder_path):
        """
        Check if folder is empty
        :param folder_path:
        :return:
        """
        try:
            files = eval(self.eval('os.listdir({})'.format(repr(folder_path))))
            logger.debug("Folder files: %s", files)
            return len(files)
        except Exception as err:
            logger.debug(str(err))
            pass

        return -1
