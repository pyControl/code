import os

# Get the directory of the current script (your_module.py)
ROOT = os.path.dirname(__file__)
VERSION = "2.0rc1"


def get_icon(icon_filename):
    return os.path.join(ROOT, "gui", "icons", f"{icon_filename}.svg")
