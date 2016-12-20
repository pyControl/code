import sys
import os
from .pycboard import Pycboard
from .run_experiment import run_experiment

# Add parent directory to path to allow import of config module.
sys.path.append(os.path.dirname(os.path.dirname(__file__))) 