import os

# ----------------------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------------------

pyControl_dir = os.path.join('..', 'pyControl') # Path to folder of pyControl framwork files.

examples_dir = os.path.join('..', 'examples')   # Path to folder of example scripts.

tasks_dir = os.path.join('..', 'tasks')         # Path to task scripts.

data_dir = os.path.join('..', 'data')           # Path to data storage folder 

config_dir = os.path.join('.', 'config')        # Path to config folder.

# ----------------------------------------------------------------------------------------
# Hardware serial ports
# ----------------------------------------------------------------------------------------

box_serials={1:'COM1'}    #Dictionary of box numbers with respective serial port addresses.

# ----------------------------------------------------------------------------------------
# Other configuration options.
# ----------------------------------------------------------------------------------------

hardware_test_display_output = False