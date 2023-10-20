import os
import json


def get_setting(setting_type, setting_name, want_default=False):
    """
    gets a user setting from settings.json or, if that doesn't exist,
    the default_user_settings dictionary
    """

    default_user_settings = {
        "folders": {
            "api_classes": os.path.join(os.getcwd(), "advanced", "api_classes"),
            "controls_dialogs": os.path.join(os.getcwd(), "advanced", "controls_dialogs"),
            "data": os.path.join(os.getcwd(), "data"),
            "devices": os.path.join(os.getcwd(), "advanced", "devices"),
            "experiments": os.path.join(os.getcwd(), "experiments"),
            "hardware_definitions": os.path.join(os.getcwd(), "advanced", "hardware_definitons"),
            "tasks": os.path.join(os.getcwd(), "tasks"),
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

    json_path = os.path.join(os.getcwd(), "settings.json")
    if os.path.exists(json_path) and not want_default:  # user has a settings.json
        with open(json_path, "r", encoding="utf-8") as f:
            custom_settings = json.loads(f.read())
        if setting_name in custom_settings[setting_type]:
            return custom_settings[setting_type][setting_name]
        else:
            return default_user_settings[setting_type][setting_name]
    else:  # use defaults
        return default_user_settings[setting_type][setting_name]


def user_folder(folder_name):
    return get_setting("folders", folder_name)
