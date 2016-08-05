import logging

from unittest import TestCase

from serial.serialutil import SerialException

import pycontrol.conf as settings
from pycontrol.board.pycboard import Pycboard

settings.LOG_HANDLER_CONSOLE_LEVEL = logging.DEBUG
settings.setup_default_logger(__name__, file_handler=False)
settings.setup_default_logger("pycontrol", file_handler=False)

class TestUploadFramework(TestCase):
    def test_upload_framework_not_found(self):
        """
        Test scenario where task_file_path is invalid
        """
        pyc = Pycboard(serial_port=settings.TEST_SERIAL_PORT)
        pyc.open_connection()  # needed for resetting filesystem

        with self.assertRaises(FileNotFoundError) as err:
            pyc.upload_framework(framework_dir='xxx')

        self.assertEqual(str(err.exception), "[Errno 2] No such file or directory: 'xxx'")

        pyc.close()

    def test_upload_framework_serial_port_not_found(self):
        """
        Test scenario were task is uploaded and serial port is not connected
        """
        pyc = Pycboard(serial_port="/dev/tty.usbmodemxxx")
        # pyc.open_connection() DO NOT OPEN CONNECTION ON PURPOSE
        with self.assertRaises(SerialException):
            pyc.upload_framework(settings.TEST_FRAMEWORK_PATH)

    def test_upload_framework(self):
        pyc = Pycboard(serial_port=settings.TEST_SERIAL_PORT)
        pyc.open_connection()
        pyc.reset_filesystem()
        pyc.upload_framework(settings.TEST_FRAMEWORK_PATH)
        self.assertTrue(pyc.framework_is_installed())
        pyc.close()
