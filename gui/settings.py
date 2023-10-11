import os
import json
import shutil
from pathlib import Path
from pyqtgraph.Qt import QtCore

VERSION = "2.0rc1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Top level pyControl folder.
settings = QtCore.QSettings("pyControl", "pyControl-app")


def setup_user_dir(new_path):
    settings.setValue("user_directory_path", new_path)
    folders = os.listdir(new_path)
    if len(folders) == 0:  # New user directory, fill with template
        for folder in ["api_classes", "controls_dialogs", "devices", "hardware_definitions", "tasks"]:
            shutil.copytree(
                Path(ROOT, "user_template", folder), Path(new_path, folder)
            )  # duplicate template folder at new destination
        Path(new_path, "data").mkdir()
        Path(new_path, "experiments").mkdir()


def get_user_directory():
    return settings.value("user_directory_path", None, type=str)


def get_setting(setting_type, setting_name, want_default=False):
    """
    gets a user setting from user_settings.json or, if that doesn't exist,
    the default_user_settings dictionary
    """

    default_user_settings = {
        "folders": {
            "data": os.path.join(get_user_directory(), "data"),
        },
        "plotting": {
            "update_interval": 10,
            "event_history_len": 200,
            "state_history_len": 100,
            "analog_history_dur": 12,
        },
        "GUI": {
            "ui_font_size": 11,
            "log_font_size": 9,
        },
    }

    json_path = os.path.join(get_user_directory(), "user_settings.json")
    if os.path.exists(json_path) and not want_default:  # user has a user_settings.json
        with open(json_path, "r", encoding="utf-8") as f:
            custom_settings = json.loads(f.read())
        if setting_name in custom_settings[setting_type]:
            return custom_settings[setting_type][setting_name]
        else:
            return default_user_settings[setting_type][setting_name]
    else:  # use defaults
        return default_user_settings[setting_type][setting_name]


def user_folder(folder_name):
    return os.path.join(get_user_directory(), folder_name)
