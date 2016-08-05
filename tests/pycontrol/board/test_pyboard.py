import logging
import loggingbootstrap

from unittest import TestCase

from pycontrol.board.pyboard_plus import PyboardPlus
import pycontrol.settings as settings

settings.LOG_HANDLER_CONSOLE_LEVEL = logging.DEBUG
loggingbootstrap.create_console_logger("pycontrol-tests", settings.LOG_HANDLER_CONSOLE_LEVEL)
loggingbootstrap.create_console_logger("pycontrol", settings.LOG_HANDLER_CONSOLE_LEVEL)


class TestPyboardPlus(TestCase):
    def test_reset_filesystem(self):
        pyb = PyboardPlus(serial_port=settings.TEST_SERIAL_PORT)
        pyb.open_connection()
        pyb.reset_filesystem()

        folder_exists = pyb.folder_exists('pyControl')
        self.assertFalse(folder_exists)

        pyb.close()

        # pyb.transfer_folder("/Users/carlos/Programador/pycontrol/framework/pyControl")
        # print(pyc.get_events())
        # print(pyc.get_states())

    def test_transfer_folder(self):
        pyb = PyboardPlus(serial_port=settings.TEST_SERIAL_PORT)

        pyb.open_connection()
        pyb.reset_filesystem()

        folder_exists = pyb.folder_exists('pyControl')
        self.assertFalse(folder_exists)

        pyb.transfer_folder(settings.TEST_FRAMEWORK_PATH)

        folder_exists = pyb.folder_exists('pyControl')
        self.assertTrue(folder_exists)

        number_of_files = pyb.folder_len('pyControl')
        self.assertTrue(number_of_files == 6)

        pyb.close()
