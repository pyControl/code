import os
import json

VERSION = "1.8"

top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Top level pyControl folder.
dirs = {
    "config": os.path.join(top_dir, "config"),
    "framework": os.path.join(top_dir, "pyControl"),
    "devices": os.path.join(top_dir, "devices"),
    "gui": os.path.join(top_dir, "gui"),
    "experiments": os.path.join(top_dir, "experiments"),
}

default_user_settings = {
    "folders": {
        "tasks": os.path.join(top_dir, "tasks"),
        "data": os.path.join(top_dir, "data"),
    },
    "plotting": {
        "update_interval": 10,
        "event_history_len": 200,
        "state_history_len": 100,
        "analog_history_dur": 12,
    },
    "other": {
        "ui_font_size": 11,
        "log_font_size": 9,
    },
}


def get_setting(setting_type, setting_name=None):
    """
    gets a user setting or group of user settings
    from the user_settings.json or, if that doesn't exist, 
    the default_user_settings dictionary
    """
    json_path = os.path.join(dirs["config"], "user_settings.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding='utf-8') as f:
            user_settings = json.loads(f.read())
    else:
        user_settings = default_user_settings
    if setting_name:
        return user_settings[setting_type][setting_name]
    return user_settings[setting_type]
