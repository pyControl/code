import os
import sys

parent_dir = os.path.dirname(os.path.dirname(__file__)) # Directory containing CLI folder.
if not parent_dir in sys.path:
    sys.path.insert(0, parent_dir) # Add parent directory to path to allow import of config module.

from .pycboard import Pycboard