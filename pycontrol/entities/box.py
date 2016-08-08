# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" pyControlAPI

"""

import logging
import pycontrol
from pycontrol.board.pycboard import Pycboard

__version__ = pycontrol.__version__
__author__ = pycontrol.__author__
__credits__ = pycontrol.__credits__
__license__ = pycontrol.__license__
__maintainer__ = pycontrol.__maintainer__
__email__ = pycontrol.__email__
__status__ = pycontrol.__status__

logger = logging.getLogger(__name__)


class Box(Pycboard):
    """
    Class that interfaces a board
    """

    def __init__(self, box_number, box_serial_port, data_file=None):
        """

        :param box_number: box number from config file
        """
        self.number = box_number
        self.data_file = data_file

        super().__init__(box_serial_port)

    # ------------------------------------------------------------------------------------
    # Data logging
    # ------------------------------------------------------------------------------------

    def open_data_file(self, file_path):
        'Open a file to write pyControl data to.'
        self.data_file = open(file_path, 'a+', newline='\n')

    def close_data_file(self):
        self.data_file.close()
        self.data_file = None

    def print_IDs(self):
        'Print state and event IDs.'
        ID_info = self.get_IDs()
        if self.data_file:  # Print IDs to file.
            self.data_file.write(ID_info)
        else:  # Print to screen.
            print(ID_info)
