# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" pycontrolapi.settings

"""

import logging

# LOGGER SETTINGS

LOG_FILENAME = "pycontrol.log"
LOG_HANDLER_FILE_LEVEL = logging.DEBUG
LOG_HANDLER_CONSOLE_LEVEL = logging.INFO

# UNIT TESTING SETTINGS
TEST_SERIAL_PORT = ""
TEST_FRAMEWORK_PATH = "" # path must end with pyControl
TEST_TASK_PATH = "" # tests are expecting blinker.py
TEST_HW_DEF_PATH = ""

try:
    from user_settings import *
except:
    pass
