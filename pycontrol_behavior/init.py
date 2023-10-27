# Check that depndencies are installed then launch the pyControl GUI.
import os
import platform
import shutil
import sys
from pycontrol_behavior import ROOT
from pathlib import Path


def add_missing_user_folders():
    required_folders = [
        "api_classes",
        "controls_dialogs",
        "devices",
        "experiments",
        "hardware_definitions",
        "tasks",
    ]
    for folder_name in required_folders:
        expected_dir = Path(current_dir, folder_name)
        if not (expected_dir.exists() and expected_dir.is_dir()):
            expected_dir.mkdir()


def setup_user_dir(new_path):
    # core folders
    for folder in ["tasks", "tools"]:
        expected_dir = Path(new_path, folder)
        if not (expected_dir.exists() and expected_dir.is_dir()):
            print("New directory created")
            shutil.copytree(Path(ROOT, "user", folder), expected_dir)  # duplicate template folder at new destination
        else:
            print("tasks exists already 👍")
    for folder in ["data", "experiments"]:
        expected_dir = Path(new_path, folder)
        if not (expected_dir.exists() and expected_dir.is_dir()):
            expected_dir.mkdir()
        else:
            print(f"{folder} exists already 👍")

    # advanced folders
    for folder in ["api_classes", "controls_dialogs", "devices", "hardware_definitions"]:
        expected_dir = Path(new_path, "advanced", folder)
        if not (expected_dir.exists() and expected_dir.is_dir()):
            print("New directory created")
            shutil.copytree(
                Path(ROOT, "user", "advanced", folder), expected_dir
            )  # duplicate template folder at new destination
        else:
            print(f"{folder} exists already 👍")

    # copy over pyw file
    gui_launch_file = "pyControl_GUI.py"
    if platform.system() == "Windows":
        shutil.copy(Path(ROOT, "user", gui_launch_file), Path(new_path, gui_launch_file+"w")) # make it a .pyw file
    else:
        shutil.copy(Path(ROOT, "user", gui_launch_file), Path(new_path, gui_launch_file))


current_dir = os.getcwd()
setup_user_dir(current_dir)
sys.exit(0)
