import logging

from unittest import TestCase

from serial.serialutil import SerialException

import pycontrol.conf as settings
from pycontrol.board.pycboard import Pycboard
from pycontrol.board.pycboard import PycboardError

settings.LOG_HANDLER_CONSOLE_LEVEL = logging.DEBUG
settings.setup_default_logger(__name__, file_handler=False)
settings.setup_default_logger("pycontrol", file_handler=False)

class TestUploadFramework(TestCase):
    def test_upload_hw_definition_not_found(self):
        """
        Test scenario where hwd_path is invalid
        """
        pyc = Pycboard(serial_port=settings.TEST_SERIAL_PORT)

        with self.assertRaises(FileNotFoundError) as err:
            pyc.upload_hardware_definition(hwd_path='xxx')

        self.assertEqual(str(err.exception), "[Errno 2] No such file or directory: 'xxx'")

    def test_upload_hw_definition_serial_port_not_found(self):
        """
        Test scenario were task is uploaded and serial port is not connected
        """
        pyc = Pycboard(serial_port="/dev/tty.usbmodemxxx")
        # pyc.open_connection() DO NOT OPEN CONNECTION ON PURPOSE
        with self.assertRaises(SerialException):
            pyc.upload_hardware_definition(hwd_path=settings.TEST_HW_DEF_PATH)

    def test_upload_hw_definition_without_framework(self):
        """
        Test scenario were hw_definition is uploaded for board where framework is not installed or is invalid
        """
        pyc = Pycboard(serial_port=settings.TEST_SERIAL_PORT)
        pyc.open_connection()
        pyc.reset_filesystem()  # ensures board is empty

        with self.assertRaises(PycboardError) as assert_err:
            pyc.upload_hardware_definition(hwd_path=settings.TEST_HW_DEF_PATH)

        expected_board_message = 'Traceback (most recent call last):\r\n  ' \
                                 'File "<stdin>", line 1, in <module>\r\n  ' \
                                 'File "hardware_definition.py", line 1, in <module>\r\n' \
                                 'ImportError: no module named \'pyControl\'\r\n'
        self.assertEqual(expected_board_message, str(assert_err.exception.board_exception))

        expected_message = "Framework not installed"
        self.assertEqual(expected_message, str(assert_err.exception))

        pyc.close()

    def test_upload_hw_definition(self):
        pyc = Pycboard(serial_port=settings.TEST_SERIAL_PORT)
        pyc.open_connection()
        pyc.reset_filesystem()
        pyc.upload_framework(settings.TEST_FRAMEWORK_PATH)
        self.assertTrue(pyc.framework_is_installed())
        pyc.upload_hardware_definition(hwd_path=settings.TEST_HW_DEF_PATH)
        pyc.close()
