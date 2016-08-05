import logging

from unittest import TestCase

from serial.serialutil import SerialException

import pycontrol.conf as settings
from pycontrol.board.pycboard import Pycboard
from pycontrol.board.pycboard import PycboardError

settings.LOG_HANDLER_CONSOLE_LEVEL = logging.DEBUG
settings.setup_default_logger(__name__, file_handler=False)
settings.setup_default_logger("pycontrol", file_handler=False)


class TestPyboardError(TestCase):
    def test_exception_parsing(self):
        error_message = 'Traceback (most recent call last):\r\n  ' \
                        'File "<stdin>", line 1, in <module>\r\n  ' \
                        'File "blinker.py", line 1, in <module>\r\n' \
                        'ImportError: no module named \'pyControl\'\r\n'

        traceback = [message.strip() for message in error_message.splitlines()]
        print(traceback)
        print(traceback[-1])


class TestUploadTask(TestCase):
    def test_upload_task_not_found(self):
        """
        Test scenario where task_file_path is invalid
        """
        pyc = Pycboard(serial_port=settings.TEST_SERIAL_PORT)

        with self.assertRaises(FileNotFoundError):
            pyc.upload_task(task_file_path='blinkerxxx.py', remove_after_install=True)

    def test_upload_task_serial_port_not_found(self):
        """
        Test scenario were task is uploaded and serial port is not connected
        """
        pyc = Pycboard(serial_port="/dev/tty.usbmodemxxx")
        # pyc.open_connection() DO NOT OPEN CONNECTION ON PURPOSE
        with self.assertRaises(SerialException):
            pyc.upload_task(task_file_path=settings.TEST_TASK_PATH, remove_after_install=True)

    def test_upload_task_without_framework(self):
        """
        Test scenario were task is uploaded for board where framework is not installed or is invalid
        """
        pyc = Pycboard(serial_port=settings.TEST_SERIAL_PORT)
        pyc.open_connection()
        pyc.reset_filesystem()  # ensures board is empty

        with self.assertRaises(PycboardError) as assert_err:
            pyc.upload_task(task_file_path=settings.TEST_TASK_PATH, remove_after_install=True)

        expected_board_message = 'Traceback (most recent call last):\r\n  ' \
                                 'File "<stdin>", line 1, in <module>\r\n  ' \
                                 'File "blinker.py", line 1, in <module>\r\n' \
                                 'ImportError: no module named \'pyControl\'\r\n'
        self.assertEqual(expected_board_message, str(assert_err.exception.board_exception))

        expected_message = "Framework not installed"
        self.assertEqual(expected_message, str(assert_err.exception))

        pyc.close()

    def test_upload_task(self):
        pyc = Pycboard(serial_port=settings.TEST_SERIAL_PORT)
        pyc.open_connection()
        pyc.reset_filesystem()
        pyc.upload_framework(settings.TEST_FRAMEWORK_PATH)
        self.assertTrue(pyc.framework_is_installed())
        pyc.upload_task(task_file_path=settings.TEST_TASK_PATH, remove_after_install=True)
        pyc.close()
